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
if PI:
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

# ################### FUNCTIONS ################### #


def get_config(*, keys):
    with open(CONFIG_FILE) as fin:
        config = load(fin)

    for key in keys:
        config = config.get(key, {})

    return config


def set_config(value, *, keys):
    with open(CONFIG_FILE) as fin:
        config = load(fin)

    target_key = keys.pop()

    for key in keys:
        config = config.get(key, {})

    config[target_key] = value


def switch_crt_on(force_switch_on=False):
    if force_switch_on or (get_config(keys=["crt", "state"]) and PI):
        _LOGGER.debug("Switching display on")
        PI.write(CRT_PIN, True)
        set_config(True, keys=["crt", "state"])
    else:
        _LOGGER.debug("Switching display on (but not really)")


def switch_crt_off(force_switch_on=False):
    if force_switch_on or (not get_config(keys=["crt", "state"]) and PI):
        _LOGGER.debug("Switching display off")
        PI.write(CRT_PIN, False)
        set_config(False, keys=["crt", "state"])
    else:
        _LOGGER.debug("Switching display off (but not really)")
