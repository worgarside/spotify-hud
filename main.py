from datetime import datetime
from html import unescape
from io import BytesIO
from json import dumps
from logging import StreamHandler, FileHandler, Formatter, getLogger, DEBUG
from os import getenv, mkdir
from os.path import exists, join, sep
from pathlib import Path
from tkinter.font import Font

from PIL import Image, ImageTk
from pychromecast import get_listed_chromecasts
from pychromecast.controllers.media import MediaStatusListener
from pychromecast.controllers.receiver import CastStatusListener
from requests import get
from sys import stdout
from tkinter import Label, Canvas, CENTER, Tk

#############
# Constants #
#############
from time import sleep

CRT_PIN = int(getenv("CRT_PIN", "-1"))
BG_COLOR = "#000000"
STANDARD_ARGS = {"highlightthickness": 0, "bd": 0, "bg": BG_COLOR}
CHAR_LIM = 31
MAX_WAIT_TIME_MS = 10000

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)

LOG_DIR = join(Path.home(), "logs", __file__.split(sep)[-2])

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

try:
    mkdir(join(Path.home(), "logs"))
except FileExistsError:
    pass

try:
    mkdir(LOG_DIR)
except FileExistsError:
    pass

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
        }

        if payload != self._previous_payload:
            self._previous_payload = payload
            update_display(payload)
        else:
            LOGGER.debug("No change to core payload")


def update_display(payload):
    global content_dict

    LOGGER.info("Updating display with payload:\t%s", dumps(payload))

    content_dict["images"]["tk_img"] = Image.open(
        BytesIO(get(payload["artwork_url"]).content)
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
                                                         "  " +
                                                         content_dict["widgets"][k][
                                                             "text"] + "  "
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
            LOGGER.error("Error connecting to Chromecast: `%s - %s`", type(exc).__name__, exc.__str__())
            sleep(10)

    # chromecast.register_status_listener(
    #     ChromecastStatusListener(chromecast.name, chromecast)
    # )
    chromecast.media_controller.register_status_listener(
        ChromecastMediaListener(chromecast.name, chromecast)
    )

    chromecast.media_controller.update_status()

    tk_root.mainloop()
    browser.stop_discovery()


if __name__ == "__main__":
    run_interface()
