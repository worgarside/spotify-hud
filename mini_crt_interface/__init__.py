from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from os import getenv
from json import dumps
from flask_scss import Scss
from pigpio import pi as rasp_pi, OUTPUT
from .api import get_tv_metadata, get_music_metadata

load_dotenv()

CRT_PIN = int(getenv('CRT_PIN'))

app = Flask(__name__)

if app.debug:
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

Scss(app, static_dir='mini_crt_interface/static/style')

MEDIA_PLAYERS = getenv('MEDIA_PLAYERS').split()

GLOBAL_CONSTANTS = {
    'media_players': dumps(MEDIA_PLAYERS),
    'hass_url': f"http://{getenv('HASS_HOST')}:{getenv('HASS_PORT')}"
    if getenv('HASS_URL') is None else getenv('HASS_URL'),
    'hass_access_token': getenv('HASS_ACCESS_TOKEN')
}


@app.route('/')
def index():
    return render_template(
        'index.html', **GLOBAL_CONSTANTS
    )


@app.route('/api/tv')
def api_tv():
    return jsonify(get_tv_metadata())


@app.route('/api/music')
def api_music():
    return jsonify(get_music_metadata())


@app.route('/no-content')
@app.route('/no_content')
def no_content():
    return render_template(
        'no_content.html', **GLOBAL_CONSTANTS
    )


@app.route('/music')
def music():
    return render_template(
        'music.html', **GLOBAL_CONSTANTS
    )


@app.route('/tv')
def tv():
    return render_template(
        'tv.html', **GLOBAL_CONSTANTS
    )


@app.route('/start')
@app.route('/crt_on')
@app.route('/crt-on')
def start_crt():
    pi = rasp_pi()
    pi.set_mode(CRT_PIN, OUTPUT)
    pi.write(CRT_PIN, True)
    pi.stop()

    return jsonify({'success': True})


@app.route('/shutdown')
@app.route('/crt_off')
@app.route('/crt-off')
def shutdown():
    pi = rasp_pi()
    pi.set_mode(CRT_PIN, OUTPUT)
    pi.write(CRT_PIN, False)
    pi.stop()

    return jsonify({'success': True})
