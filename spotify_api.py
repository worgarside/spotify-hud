from datetime import datetime, timedelta
from json import load, dumps, dump
from logging import StreamHandler, FileHandler, Formatter, getLogger, DEBUG
from os import getenv, mkdir
from os.path import join, abspath, dirname, sep
from pathlib import Path

from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from sys import stdout
from wg_utilities.helpers.functions import get_proj_dirs
from wg_utilities.references.constants import WGSCRIPTS as PROJ_NAME
from wg_utilities.services.services import pb_notify

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)

LOG_DIR = f"{Path.home()}/logs/{__file__.split(sep)[-1].split('.')[0]}"

try:
    mkdir(f"{Path.home()}/logs")
except FileExistsError:
    pass

try:
    mkdir(LOG_DIR)
except FileExistsError:
    pass

TODAY_STR = datetime.today().strftime("%Y-%m-%d")

SEVEN_DAYS_BEHIND = datetime.today() - timedelta(days=7)
SEVEN_DAYS_FORWARD = datetime.today() + timedelta(days=7)

SH = StreamHandler(stdout)
FH = FileHandler(f"{LOG_DIR}/{TODAY_STR}.log")

FORMATTER = Formatter(
    "%(asctime)s\t%(name)s\t[%(levelname)s]\t%(message)s", "%Y-%m-%d %H:%M:%S"
)
FH.setFormatter(FORMATTER)
SH.setFormatter(FORMATTER)
LOGGER.addHandler(FH)
LOGGER.addHandler(SH)

load_dotenv(join(abspath(dirname(__file__)), ".env"))

PB_PARAMS = {"token": getenv("PB_API_KEY"), "t": "Spotify - New Release"}


CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

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
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://localhost:8080",
        scope=",".join(ALL_SCOPES),
        cache_path=join(abspath(dirname(__file__)), "spotify_cache.json"),
    )
)

def main():
    print(dumps(SPOTIFY.current_user_playing_track(), indent=4))


if __name__ == '__main__':
    main()