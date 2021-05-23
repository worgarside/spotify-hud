from html import unescape
from io import BytesIO
from json import dumps, load
from logging import getLogger, DEBUG
from os import mkdir
from os.path import exists, join
from pathlib import Path
from re import compile as compile_regex
from tkinter import Label, Canvas, CENTER, Tk
from tkinter.font import Font

from PIL import Image, ImageTk
from dotenv import load_dotenv
from requests import get

from const import CONFIG_FILE, FH, SH, PI, CRT_PIN

load_dotenv()

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)
LOGGER.addHandler(FH)
LOGGER.addHandler(SH)


class CrtTv:
    BG_COLOR = "#000000"
    STANDARD_ARGS = {"highlightthickness": 0, "bd": 0, "bg": BG_COLOR}
    CHAR_LIM = 31
    MAX_WAIT_TIME_MS = 10000
    ARTWORK_DIR = join(Path.home(), "crt_artwork")
    PATTERN = compile_regex("[^\w ]+")

    def __init__(self):
        if not exists(self.ARTWORK_DIR):
            mkdir(self.ARTWORK_DIR)

        self.root = Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg=self.BG_COLOR)

        crt_font = Font(family="Courier New", size=int(0.05 * self.screen_height))

        self.content_dict = {
            "images": {"tk_img": None, "artwork": ""},
            "widgets": {
                "canvas": Canvas(
                    self.root,
                    width=self.screen_width,
                    height=self.screen_height,
                    **self.STANDARD_ARGS,
                )
            },
            "coords": {
                "media_title": {
                    "x": 0.5 * self.screen_width,
                    "y": 0.8 * self.screen_height,
                    "anchor": CENTER,
                },
                "media_artist": {
                    "x": 0.5 * self.screen_width,
                    "y": 0.9 * self.screen_height,
                    "anchor": CENTER,
                },
            },
        }
        self.content_dict["widgets"]["canvas"].place(
            x=0, y=0, width=self.screen_width, height=self.screen_height
        )

        self.content_dict["widgets"]["artwork"] = Label(
            self.content_dict["widgets"]["canvas"], image="", **self.STANDARD_ARGS
        )

        self.content_dict["widgets"]["media_title"] = Label(
            self.content_dict["widgets"]["canvas"],
            text="",
            font=crt_font,
            fg="#ffffff",
            bg=self.BG_COLOR,
        )

        self.content_dict["widgets"]["media_artist"] = Label(
            self.content_dict["widgets"]["canvas"],
            text="",
            font=crt_font,
            fg="#ffffff",
            bg=self.BG_COLOR,
        )

        self.content_dict["widgets"]["artwork"].place(
            x=0.5 * self.screen_width,
            y=(0.5 * self.artwork_size) + (0.075 * self.screen_height),
            anchor=CENTER,
        )
        self.content_dict["widgets"]["media_title"].place(
            **self.content_dict["coords"]["media_title"]
        )
        self.content_dict["widgets"]["media_artist"].place(
            **self.content_dict["coords"]["media_artist"]
        )

    def update_display(self, payload):
        LOGGER.info("Updating display with payload:\t%s", dumps(payload))

        if not exists(
            artist_dir := join(
                self.ARTWORK_DIR,
                self.PATTERN.sub("", payload["media_artist"]).lower().replace(" ", "_"),
            )
        ):
            mkdir(artist_dir)
            LOGGER.info(
                "Created artwork directory for `%s`: `%s`",
                payload["media_artist"],
                artist_dir,
            )

        self.artwork_path = join(
            artist_dir,
            self.PATTERN.sub("", payload["album_name"] or payload["media_title"])
            .lower()
            .replace(" ", "_"),
        )

        try:
            with open(self.artwork_path, "rb") as fin:
                self.content_dict["images"]["tk_img"] = Image.open(BytesIO(fin.read()))
            LOGGER.debug("Retrieved artwork from `%s`", self.artwork_path)
        except FileNotFoundError:
            artwork_bytes = get(payload["artwork_url"]).content
            self.content_dict["images"]["tk_img"] = Image.open(BytesIO(artwork_bytes))

            with open(self.artwork_path, "wb") as fout:
                fout.write(artwork_bytes)

            LOGGER.info(
                "Saved artwork for `%s` by `%s` to `%s`",
                payload["album_name"],
                payload["media_artist"],
                self.artwork_path,
            )
        except Exception as exc:
            LOGGER.error(
                "Unable to get artwork: `%s - %s`",
                type(exc).__name__,
                exc.__str__(),
            )

        self.content_dict["images"]["tk_img"] = self.content_dict["images"][
            "tk_img"
        ].resize((self.artwork_size, self.artwork_size), Image.ANTIALIAS)
        self.content_dict["images"]["artwork"] = ImageTk.PhotoImage(
            self.content_dict["images"]["tk_img"]
        )

        self.content_dict["widgets"]["artwork"].configure(
            image=self.content_dict["images"]["artwork"]
        )

        for k, v in payload.items():
            if k in self.content_dict["widgets"]:
                self.content_dict["widgets"][k].config(text=unescape(v))
                if len(self.content_dict["widgets"][k]["text"]) > self.CHAR_LIM:
                    self.content_dict["widgets"][k]["text"] = (
                        "  " + self.content_dict["widgets"][k]["text"] + "  "
                    ) * 3

                    self.hscroll_label(k)

    def hscroll_label(self, k):
        self.content_dict["coords"][k]["x"] -= 2

        self.content_dict["coords"][k]["x"] = (
            0.5 * self.screen_width
            if self.content_dict["coords"][k]["x"]
            < (0.5 * self.screen_width)
            - (self.content_dict["widgets"][k].winfo_width() / 3)
            else self.content_dict["coords"][k]["x"]
        )

        self.content_dict["widgets"][k].place(**self.content_dict["coords"][k])

        if len(self.content_dict["widgets"][k]["text"]) > self.CHAR_LIM:
            self.content_dict["widgets"]["canvas"].after(10, self.hscroll_label, k)
        else:
            self.content_dict["coords"][k]["x"] = 0.5 * self.screen_width
            self.content_dict["widgets"][k].place(**self.content_dict["coords"][k])

    def get_config(self, *, keys):
        with open(CONFIG_FILE) as fin:
            config = load(fin)

        for key in keys:
            config = config.get(key, {})

        return config

    def switch_on(self):
        if self.get_config(keys=["crt", "state"]) and PI is not None:
            LOGGER.debug("Switching display on")
            PI.write(CRT_PIN, True)
        else:
            LOGGER.debug("Switching display on (but not really)")

    def switch_off(self):
        if not self.get_config(keys=["crt", "state"]) and PI is not None:
            LOGGER.debug("Switching display off")
            PI.write(CRT_PIN, False)
        else:
            LOGGER.debug("Switching display off (but not really)")

    @property
    def screen_width(self):
        return self.root.winfo_screenwidth()

    @property
    def screen_height(self):
        return self.root.winfo_screenheight()

    @property
    def artwork_size(self):
        return int(0.65 * self.screen_height)
