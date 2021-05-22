from datetime import datetime
from os import mkdir
from os.path import exists, join
from pathlib import Path

LOG_DIR = join(Path.home(), "logs", "smart-mini-crt-interface")
TODAY_STR = datetime.today().strftime("%Y-%m-%d")


for _dir in [join(Path.home(), "logs"), LOG_DIR]:
    if not exists(_dir):
        mkdir(_dir)
