from json import load, dump
from logging import getLogger, DEBUG

from flask import Flask
from os import getenv

from const import CONFIG_FILE, FH, SH, switch_crt_on, switch_crt_off, set_config

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)
LOGGER.addHandler(FH)
LOGGER.addHandler(SH)

LOGGER.debug("Config file is `%s`", CONFIG_FILE)

app = Flask(__name__)
app.config["DEBUG"] = True


@app.route("/crt/on", methods=["GET"])
def crt_on():
    with open(CONFIG_FILE) as fin:
        config = load(fin)

    config["crt"]["state"] = True

    with open(CONFIG_FILE, "w") as fout:
        dump(config, fout)

    switch_crt_on()

    return "<p>CRT On</p>"


@app.route("/crt/off", methods=["GET"])
def crt_off():
    with open(CONFIG_FILE) as fin:
        config = load(fin)

    config["crt"]["state"] = False

    with open(CONFIG_FILE, "w") as fout:
        dump(config, fout)

    switch_crt_off()

    return "<p>CRT Off</p>"


@app.route("/crt/toggle", methods=["GET"])
def crt_toggle():
    with open(CONFIG_FILE) as fin:
        config = load(fin)

    config["crt"]["state"] = not config["crt"]["state"]

    with open(CONFIG_FILE, "w") as fout:
        dump(config, fout)

    if config["crt"]["state"]:
        switch_crt_on()
    else:
        switch_crt_off()

    return f"""<p>CRT {"On" if config["crt"]["state"] else "Off"}</p>"""


@app.route("/nanoleaf-mirror/on", methods=["GET"])
def nanoleaf_on():
    with open(CONFIG_FILE) as fin:
        config = load(fin)

    config["nanoleafControl"]["state"] = True

    with open(CONFIG_FILE, "w") as fout:
        dump(config, fout)

    set_config(True, keys=["nanoleafControl", "state"])

    return "<p>Nanoleaf Control On</p>"


@app.route("/nanoleaf-mirror/off", methods=["GET"])
def nanoleaf_off():
    with open(CONFIG_FILE) as fin:
        config = load(fin)

    config["nanoleafControl"]["state"] = False

    with open(CONFIG_FILE, "w") as fout:
        dump(config, fout)

    set_config(False, keys=["nanoleafControl", "state"])

    return "<p>Nanoleaf Control Off</p>"


@app.route("/nanoleaf-mirror/toggle", methods=["GET"])
def nanoleaf_toggle():
    with open(CONFIG_FILE) as fin:
        config = load(fin)

    config["nanoleafControl"]["state"] = not config["crt"]["state"]

    with open(CONFIG_FILE, "w") as fout:
        dump(config, fout)

    if config["nanoleafControl"]["state"]:
        set_config(True, keys=["nanoleafControl", "state"])
    else:
        set_config(False, keys=["nanoleafControl", "state"])

    return f"""<p>Nanoleaf Control {"On" if config["crt"]["state"] else "Off"}</p>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(getenv("CRT_API_PORT", "5000")))
