from logging import StreamHandler, FileHandler, Formatter, getLogger, DEBUG
from os import getenv, environ
from re import sub

from PIL import Image
from dotenv import load_dotenv
from nanoleafapi import Nanoleaf
from pychromecast import get_listed_chromecasts
from pychromecast.controllers.media import (
    MediaStatusListener,
    MEDIA_PLAYER_STATE_PLAYING,
    MEDIA_PLAYER_STATE_BUFFERING,
    MEDIA_PLAYER_STATE_PAUSED,
    MEDIA_PLAYER_STATE_IDLE,
    MEDIA_PLAYER_STATE_UNKNOWN,
)
from pychromecast.controllers.receiver import CastStatusListener
from sys import stdout
from time import sleep

from const import LOG_DIR, TODAY_STR
from crt_tv import CrtTv

load_dotenv()

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)

SH = StreamHandler(stdout)
FH = FileHandler(f"{LOG_DIR}/{TODAY_STR}.log")

FORMATTER = Formatter(
    "%(asctime)s\t%(name)s\t[%(levelname)s]\t%(message)s", "%Y-%m-%d %H:%M:%S"
)
FH.setFormatter(FORMATTER)
SH.setFormatter(FORMATTER)
LOGGER.addHandler(FH)
LOGGER.addHandler(SH)

if (display_ev := getenv("DISPLAY")) in {None, "0.0"}:
    LOGGER.warning("No display found. Using :0.0")
    environ.__setitem__("DISPLAY", ":0.0")
else:
    LOGGER.debug("`DISPLAY` env var is set to: %s", display_ev)

#############
# Constants #
#############

CAST_NAME = "Hi-fi System"

try:
    from pigpio import pi as rasp_pi, OUTPUT

    pi = rasp_pi()
    pi.set_mode(CrtTv.CRT_PIN, OUTPUT)

    def switch_on():
        LOGGER.debug("Switching display on")
        pi.write(CrtTv.CRT_PIN, True)

    def switch_off():
        LOGGER.debug("Switching display off")
        pi.write(CrtTv.CRT_PIN, False)


except (AttributeError, ModuleNotFoundError):

    def switch_on():
        LOGGER.debug("Switching display on (but not really)")

    def switch_off():
        LOGGER.debug("Switching display off (but not really)")


CRT = CrtTv()

SHAPES = Nanoleaf(getenv("NANOLEAF_SHAPES_IP"), getenv("NANOLEAF_SHAPES_AUTH_TOKEN"))


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
            )[0].url
            if status.images
            else None,
            "media_title": sub(r".mp3$", "", status.title or ""),
            "media_artist": status.artist or "",
            "album_name": status.album_name,
        }

        if status.player_state in {
            MEDIA_PLAYER_STATE_PLAYING,
            MEDIA_PLAYER_STATE_PAUSED,
            MEDIA_PLAYER_STATE_BUFFERING,
            MEDIA_PLAYER_STATE_IDLE,
        }:
            LOGGER.info(
                "MediaStatus.player_state is `%s`. Switching on", status.player_state
            )
            switch_on()

            if payload != self._previous_payload:
                self._previous_payload = payload
                CRT.update_display(payload)

                SHAPES.write_effect(
                    {
                        "command": "display",
                        "animType": "random",
                        "colorType": "HSB",
                        "animData": None,
                        "palette": get_n_colors_from_image(CRT.artwork_path),
                        "transTime": {"minValue": 50, "maxValue": 100},
                        "delayTime": {"minValue": 50, "maxValue": 100},
                        "loop": True,
                    }
                )
            else:
                LOGGER.debug("No change to core payload")

        elif status.player_state in {
            MEDIA_PLAYER_STATE_UNKNOWN,
        }:
            LOGGER.info(
                "MediaStatus.player_state is `%s`. Switching off", status.player_state
            )
            switch_off()
        else:
            LOGGER.error(
                "`MediaStatus.player_state` in unexpected stater: `%s`",
                status.player_state,
            )


def get_n_colors_from_image(img_path, n=15):
    pixels = Image.open(img_path).quantize(colors=n, method=0)

    # pixels.show()

    return [
        {
            "hue": color_tuple[0],
            "saturation": int((color_tuple[1] * 100) / 255),
            "brightness": int((color_tuple[2] * 100) / 255),
        }
        for count, color_tuple in sorted(
            pixels.convert(mode="HSV").getcolors(),
            key=lambda elem: elem[0],
            reverse=True,
        )
    ][:n]


def run_interface():
    chromecast = None
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

    chromecast.media_controller.register_status_listener(
        ChromecastMediaListener(chromecast.name, chromecast)
    )

    LOGGER.info("Chromecast connected and status listener registered")

    chromecast.media_controller.update_status()

    LOGGER.info("Status updated, starting TK mainloop")

    CRT.root.mainloop()

    LOGGER.info("TK mainloop exited, stopping Chromecast discovery")

    browser.stop_discovery()

    LOGGER.info("Exiting")


if __name__ == "__main__":
    run_interface()
