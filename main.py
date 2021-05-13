from datetime import datetime
from html import unescape
from io import BytesIO
from json import dumps
from logging import StreamHandler, FileHandler, Formatter, getLogger, DEBUG
from os import getenv, mkdir
from os.path import exists, join
from pathlib import Path
from re import compile as compile_regex
from tkinter import Label, Canvas, CENTER, Tk
from tkinter.font import Font

from PIL import Image, ImageTk
from dotenv import load_dotenv
from pychromecast import get_listed_chromecasts
from pychromecast.controllers.media import MediaStatusListener
from pychromecast.controllers.receiver import CastStatusListener
from requests import get
from sys import stdout
from time import sleep

load_dotenv()

#############
# Constants #
#############

CRT_PIN = int(getenv("CRT_PIN", "-1"))
BG_COLOR = "#000000"
STANDARD_ARGS = {"highlightthickness": 0, "bd": 0, "bg": BG_COLOR}
CHAR_LIM = 31
MAX_WAIT_TIME_MS = 10000

PATTERN = compile_regex("[^\w ]+")

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)

LOG_DIR = join(Path.home(), "logs", "smart-mini-crt-interface")
ARTWORK_DIR = join(Path.home(), "crt_artwork")

try:
    from pigpio import pi as rasp_pi, OUTPUT

    pi = rasp_pi()
    pi.set_mode(CRT_PIN, OUTPUT)

    def switch_on():
        LOGGER.debug("Switching display on")
        pi.write(CRT_PIN, True)

    def switch_off():
        LOGGER.debug("Switching display off")
        pi.write(CRT_PIN, False)


except (AttributeError, ModuleNotFoundError):

    def switch_on():
        LOGGER.debug("Switching display on (but not really)")

    def switch_off():
        LOGGER.debug("Switching display off (but not really)")


# Change to the friendly name of your Chromecast
CAST_NAME = "Hi-fi System"

for _dir in [join(Path.home(), "logs"), LOG_DIR, ARTWORK_DIR]:
    if not exists(_dir):
        mkdir(_dir)

TODAY_STR = datetime.today().strftime("%Y-%m-%d")

SH = StreamHandler(stdout)
FH = FileHandler(f"{LOG_DIR}/{TODAY_STR}.log")

FORMATTER = Formatter(
    "%(asctime)s\t%(name)s\t[%(levelname)s]\t%(message)s", "%Y-%m-%d %H:%M:%S"
)
FH.setFormatter(FORMATTER)
SH.setFormatter(FORMATTER)
LOGGER.addHandler(FH)
LOGGER.addHandler(SH)

###########
# Globals #
###########

image_size: float = 0
content_dict = {}
dims = (0, 0)

chromecast = None
browser = None


class ChromecastStatusListener(CastStatusListener):
    def __init__(self, name, cast):
        self.name = name
        self.cast = cast

    def new_cast_status(self, status):
        pass


class ChromecastMediaListener(MediaStatusListener):
    def __init__(self, name, cast):
        self.name = name
        self.cast = cast

        self._previous_payload = dict()

    def new_media_status(self, status):
        payload = {
            "artwork_url": sorted(
                status.images, key=lambda img: img.height, reverse=True
            )[0].url,
            "media_title": status.title,
            "media_artist": status.artist,
            "album_name": status.album_name,
        }

        if payload != self._previous_payload:
            self._previous_payload = payload
            update_display(payload)
        else:
            LOGGER.debug("No change to core payload")


def update_display(payload):
    global content_dict

    LOGGER.info("Updating display with payload:\t%s", dumps(payload))

    if not exists(
        artist_dir := join(
            ARTWORK_DIR,
            PATTERN.sub("", payload["media_artist"]).lower().replace(" ", "_"),
        )
    ):
        mkdir(artist_dir)
        LOGGER.info("Created artwork directory for `%s`", payload["media_artist"])

    artwork_path = join(
        artist_dir,
        PATTERN.sub("", payload["album_name"]).lower().replace(" ", "_"),
    )

    try:
        with open(artwork_path, "rb") as fin:
            content_dict["images"]["tk_img"] = Image.open(BytesIO(fin.read()))
        LOGGER.debug("Retrieved artwork from `%s`", artwork_path)
    except FileNotFoundError:
        artwork_bytes = get(payload["artwork_url"]).content
        content_dict["images"]["tk_img"] = Image.open(BytesIO(artwork_bytes))
        with open(artwork_path, "wb") as fout:
            fout.write(artwork_bytes)

        LOGGER.info(
            "Saved artwork for `%s` by `%s` to `%s`",
            payload["album_name"],
            payload["media_artist"],
            artwork_path,
        )

    except Exception as exc:
        LOGGER.error(
            "Unable to get artwork: `%s - %s`",
            type(exc).__name__,
            exc.__str__(),
        )

    content_dict["images"]["tk_img"] = content_dict["images"]["tk_img"].resize(
        (image_size, image_size), Image.ANTIALIAS
    )
    content_dict["images"]["artwork"] = ImageTk.PhotoImage(
        content_dict["images"]["tk_img"]
    )

    content_dict["widgets"]["artwork"].configure(
        image=content_dict["images"]["artwork"]
    )

    for k, v in payload.items():
        if k in content_dict["widgets"]:
            content_dict["widgets"][k].config(text=unescape(v))
            if len(content_dict["widgets"][k]["text"]) > CHAR_LIM:
                content_dict["widgets"][k]["text"] = (
                    "  " + content_dict["widgets"][k]["text"] + "  "
                ) * 3

                hscroll_label(k)

    switch_on()


def hscroll_label(k):
    global content_dict

    content_dict["coords"][k]["x"] -= 2

    content_dict["coords"][k]["x"] = (
        0.5 * dims[0]
        if content_dict["coords"][k]["x"]
        < (0.5 * dims[0]) - (content_dict["widgets"][k].winfo_width() / 3)
        else content_dict["coords"][k]["x"]
    )

    content_dict["widgets"][k].place(**content_dict["coords"][k])

    if len(content_dict["widgets"][k]["text"]) > CHAR_LIM:
        content_dict["widgets"]["canvas"].after(10, hscroll_label, k)
    else:
        content_dict["coords"][k]["x"] = 0.5 * dims[0]
        content_dict["widgets"][k].place(**content_dict["coords"][k])


def initialize_gui():
    global image_size, content_dict, dims

    root = Tk()
    root.attributes("-fullscreen", True)
    root.configure(bg=BG_COLOR)

    dims = root.winfo_screenwidth(), root.winfo_screenheight()

    image_size = int(0.65 * dims[1])

    crt_font = Font(family="Courier New", size=int(0.05 * dims[1]))

    content_dict = {
        "images": {"tk_img": None, "artwork": ""},
        "widgets": {
            "canvas": Canvas(root, width=dims[0], height=dims[1], **STANDARD_ARGS)
        },
        "coords": {
            "media_title": {"x": 0.5 * dims[0], "y": 0.8 * dims[1], "anchor": CENTER},
            "media_artist": {"x": 0.5 * dims[0], "y": 0.9 * dims[1], "anchor": CENTER},
        },
    }
    content_dict["widgets"]["canvas"].place(x=0, y=0, width=dims[0], height=dims[1])

    content_dict["widgets"]["artwork"] = Label(
        content_dict["widgets"]["canvas"], image="", **STANDARD_ARGS
    )

    content_dict["widgets"]["media_title"] = Label(
        content_dict["widgets"]["canvas"],
        text="",
        font=crt_font,
        fg="#ffffff",
        bg=BG_COLOR,
    )

    content_dict["widgets"]["media_artist"] = Label(
        content_dict["widgets"]["canvas"],
        text="",
        font=crt_font,
        fg="#ffffff",
        bg=BG_COLOR,
    )

    content_dict["widgets"]["artwork"].place(
        x=0.5 * dims[0], y=(0.5 * image_size) + (0.075 * dims[1]), anchor=CENTER
    )
    content_dict["widgets"]["media_title"].place(
        **content_dict["coords"]["media_title"]
    )
    content_dict["widgets"]["media_artist"].place(
        **content_dict["coords"]["media_artist"]
    )

    return root


def run_interface():
    global chromecast, browser

    tk_root = initialize_gui()

    LOGGER.info("Connecting to Chromecast...")

    while chromecast is None:
        try:
            _chromecasts, browser = get_listed_chromecasts(
                friendly_names=[CAST_NAME],
            )

            chromecast = _chromecasts.pop()
            # Start socket client's worker thread and wait for initial status update
            chromecast.wait()
        except Exception as exc:
            LOGGER.error(
                "Error connecting to Chromecast: `%s - %s`",
                type(exc).__name__,
                exc.__str__(),
            )
            sleep(10)

    # chromecast.register_status_listener(
    #     ChromecastStatusListener(chromecast.name, chromecast)
    # )
    chromecast.media_controller.register_status_listener(
        ChromecastMediaListener(chromecast.name, chromecast)
    )

    LOGGER.info("Chromecast connected and status listener registered")

    chromecast.media_controller.update_status()

    LOGGER.info("Status updated, starting TK mainloop")

    tk_root.mainloop()

    LOGGER.info("TK mainloop exited, stopping Chromecast discovery")

    browser.stop_discovery()

    LOGGER.info("Exiting")


if __name__ == "__main__":
    run_interface()
