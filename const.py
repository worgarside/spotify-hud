from datetime import datetime
from json import dump, load
from logging import StreamHandler, FileHandler, Formatter, getLogger, DEBUG
from os import mkdir, getenv
from os.path import exists, join, abspath, dirname
from pathlib import Path

from dotenv import load_dotenv
from sys import stdout

try:
    from pigpio import pi as rasp_pi, OUTPUT
except (AttributeError, ModuleNotFoundError):
    rasp_pi = lambda *a, **kw: None
    OUTPUT = None

load_dotenv()

# ################### CONSTANT VALUES ################### #

TODAY_STR = datetime.today().strftime("%Y-%m-%d")

CRT_PIN = int(getenv("CRT_PIN", "-1"))

CAST_NAME = "Hi-fi System"

PI = rasp_pi()
PI.set_mode(CRT_PIN, OUTPUT)

# ################### DIRECTORIES / FILES ################### #

LOG_DIR = join(Path.home(), "logs", "smart-mini-crt-interface")

for _dir in [join(Path.home(), "logs"), LOG_DIR]:
    if not exists(_dir):
        mkdir(_dir)

CONFIG_FILE = join(abspath(dirname(__file__)), "../config.json")

_DEFAULT_CONFIG = {"crt": {"state": None}}

if not exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as fout:
        dump(_DEFAULT_CONFIG, fout)
else:

    def _add_keys_to_dict(input_dict, output_dict):
        for k, v in input_dict.items():
            if k not in output_dict:
                output_dict[k] = v
            elif isinstance(v, dict):
                _add_keys_to_dict(v, output_dict[k])

    with open(CONFIG_FILE) as fin:
        loaded_config = load(fin)

    _add_keys_to_dict(_DEFAULT_CONFIG, loaded_config)

    with open(CONFIG_FILE, "w") as fout:
        dump(loaded_config, fout)

# ################### LOGGING ################### #

SH = StreamHandler(stdout)
FH = FileHandler(f"{LOG_DIR}/{TODAY_STR}.log")

FORMATTER = Formatter(
    "%(asctime)s\t%(name)s\t[%(levelname)s]\t%(message)s", "%Y-%m-%d %H:%M:%S"
)

FH.setFormatter(FORMATTER)
SH.setFormatter(FORMATTER)

_LOGGER = getLogger(__name__)
_LOGGER.setLevel(DEBUG)
_LOGGER.addHandler(FH)
_LOGGER.addHandler(SH)
