from os import getenv

from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from flask_scss import Scss
from pigpio import pi as rasp_pi, OUTPUT

from .api import get_tv_metadata, get_music_metadata

load_dotenv()

CRT_PIN = int(getenv('CRT_PIN'))

app = Flask(__name__)

if app.debug:
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

Scss(app, static_dir='mini_crt_interface/static/style')

pi = rasp_pi()
pi.set_mode(CRT_PIN, OUTPUT)


@app.route('/')
@app.route('/no-content')
@app.route('/no_content')
def no_content():
    return render_template(
        'no_content.html'
    )


@app.route('/api/tv')
def api_tv():
    return jsonify(get_tv_metadata())


@app.route('/api/music')
def api_music():
    return jsonify(get_music_metadata())


@app.route('/music')
def music():
    return render_template(
        'music.html'
    )


@app.route('/tv')
def tv():
    return render_template(
        'tv.html'
    )


@app.route('/start')
@app.route('/crt_on')
@app.route('/crt-on')
def start_crt():
    pi.write(CRT_PIN, True)
    return jsonify({'success': True})


@app.route('/shutdown')
@app.route('/crt_off')
@app.route('/crt-off')
def shutdown():
    pi.write(CRT_PIN, False)
    return jsonify({'success': True})
