from datetime import datetime
from html import unescape
from io import BytesIO
from json import load, dump
from logging import StreamHandler, FileHandler, Formatter, getLogger, DEBUG
from os import getenv, mkdir
from os.path import exists, join, abspath, dirname, sep
from pathlib import Path
from sys import stdout
from tkinter import *
from tkinter.font import Font

from PIL import Image, ImageTk
from dotenv import load_dotenv
from requests import get
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

load_dotenv(join(abspath(dirname(__file__)), ".env"))

#############
# Constants #
#############

CRT_PIN = int(getenv("CRT_PIN"))
BG_COLOR = "#000000"
STANDARD_ARGS = {"highlightthickness": 0, "bd": 0, "bg": BG_COLOR}
CHAR_LIM = 31
MAX_WAIT_TIME_MS = 10000

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)

LOG_DIR = f"{Path.home()}/logs/{__file__.split(sep)[-2]}"

PAYLOAD_CACHE = "/tmp/crt_payload.json"

if not exists(PAYLOAD_CACHE):
    with open(PAYLOAD_CACHE, "w") as fout:
        fout.write(str(dict()))

try:
    mkdir(f"{Path.home()}/logs")
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

ALL_SCOPES = [
    "ugc-image-upload",
    "user-read-recently-played",
    "user-top-read",
    "user-read-playback-position",
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "app-remote-control",
    "streaming",
    "playlist-modify-public",
    "playlist-modify-private",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-follow-modify",
    "user-follow-read",
    "user-library-modify",
    "user-library-read",
    "user-read-email",
    "user-read-private",
]

SPOTIFY = Spotify(
    auth_manager=SpotifyOAuth(
        client_id=getenv("SPOTIFY_CLIENT_ID"),
        client_secret=getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://localhost:8080",
        scope=",".join(ALL_SCOPES),
        cache_path=join(abspath(dirname(__file__)), "spotify_cache.json"),
    )
)

###########
# Globals #
###########

image_size: float = 0
content_dict = {}
dims = (0, 0)

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


def update_display(payload):
    global content_dict

    content_dict["images"]["tk_img"] = Image.open(
        BytesIO(get(payload["attributes"]["artwork_url"]).content)
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

    for k, v in payload["attributes"].items():
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


def execute_command(payload):
    command_dict = {"switch_on": switch_on, "switch_off": switch_off}

    if payload["attributes"]["command"] in command_dict:
        command_dict[payload["attributes"]["command"]]()
    else:
        raise ValueError("Command not found")


def get_update(force_update=False):
    res = SPOTIFY.current_user_playing_track()

    time_remaining = res.get("item", {}).get("duration_ms", 30000) - res.get(
        "progress_ms", 0
    )

    if not res.get("is_playing", False):
        switch_off()
        return time_remaining

    for img in sorted(
        res["item"]["album"]["images"], key=lambda i: i["height"], reverse=True
    ):
        if img["height"] >= 300:
            artwork_url = img["url"]
            break
    else:
        artwork_url = "https://via.placeholder.com/300"

    media_title = res.get("item", {}).get("album", {}).get("name", "?")
    media_artists = ", ".join(
        artist.get("name", "?")
        for artist in res.get("item", {}).get("album", {}).get("artists", [])
    )

    payload = {
        "attributes": {
            "artwork_url": artwork_url,
            "media_title": media_title,
            "media_artist": media_artists,
        }
    }

    with open(PAYLOAD_CACHE) as fin:
        prev_payload = load(fin)

    if payload != prev_payload or force_update:
        with open("/tmp/crt_payload.json", "w") as fout:
            dump(payload, fout)

        LOGGER.info("Updating display for '%s' by '%s'", media_title, media_artists)

        update_display(payload)

    else:
        LOGGER.debug("No change, moving on")

    return time_remaining


def initialize():
    global image_size, content_dict, dims

    switch_on()

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


def refresher(root):
    LOGGER.debug("Refreshing")

    time_remaining_ms = get_update()

    root.after(min(MAX_WAIT_TIME_MS, time_remaining_ms), refresher, root)


if __name__ == "__main__":
    tk_root = initialize()
    refresher(tk_root)
    get_update(True)
    tk_root.mainloop()
