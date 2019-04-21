from flask import Flask, render_template
from dotenv import load_dotenv
from os import getenv
from json import dumps
from flask_scss import Scss

load_dotenv()

app = Flask(__name__)

if app.debug:
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

Scss(app, static_dir='spotify_hud/static/style')

MEDIA_PLAYERS = getenv('MEDIA_PLAYERS').split()


@app.route('/')
def index():
    return render_template(
        'index.html'
    )


@app.route('/no-content')
def no_content():
    return render_template(
        'no_content.html'
    )


@app.route('/music')
def music():
    return render_template(
        'music.html',
        media_players=dumps(MEDIA_PLAYERS),
        hass_url=f"http://{getenv('HASS_HOST')}:{getenv('HASS_PORT')}",
        hass_access_token=getenv('HASS_ACCESS_TOKEN')
    )

