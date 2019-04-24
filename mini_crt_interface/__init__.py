from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from os import getenv
from json import dumps
from flask_scss import Scss

load_dotenv()

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


@app.route('/shutdown')
def shutdown():
    print('shutting down bye bye')
    return jsonify({'shutdown': True})
