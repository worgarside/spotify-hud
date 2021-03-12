from base64 import b64decode
from html import unescape
from io import BytesIO
from json import loads
from os import getenv
from tkinter import *
from tkinter.font import Font
from traceback import format_exc

from PIL import Image, ImageTk
from dotenv import load_dotenv
from paho.mqtt.client import Client
from pigpio import pi as rasp_pi, OUTPUT
from requests import post

load_dotenv()

#############
# Constants #
#############

MQTT_BROKER = getenv('HASS_HOST')
MQTT_CREDS = {
    'username': getenv('MQTT_USERNAME'),
    'password': getenv('MQTT_PASSWORD')
}
MQTT_TOPIC = getenv('MQTT_TOPIC')
PB_PARAMS = {
    'token': getenv('PB_API_KEY'),
    't': 'CRT MQTT Alert'
}
SPEAKERS = ['media_player.all_speakers', 'media_player.hifi_system']
CRT_PIN = int(getenv('CRT_PIN'))
BG_COLOR = '#000000'
STANDARD_ARGS = {'highlightthickness': 0, 'bd': 0, 'bg': BG_COLOR}
CHAR_LIM = 31

###########
# Globals #
###########

image_size: float = 0
content_dict = {}
dims = (0, 0)

try:
    pi = rasp_pi()
    pi.set_mode(CRT_PIN, OUTPUT)


    def switch_on():
        pi.write(CRT_PIN, True)


    def switch_off():
        pi.write(CRT_PIN, False)
except AttributeError:
    def switch_on():
        pass


    def switch_off():
        pass


def pb_notify(m, t, token):
    post(
        'https://api.pushbullet.com/v2/pushes',
        headers={
            'Access-Token': token,
            'Content-Type': 'application/json'
        },
        json={
            'body': m,
            'title': t,
            'type': 'note'
        }
    )


def update_display(payload):
    global content_dict

    base64_encoded_string = unescape(payload['attributes']['artwork'])
    content_dict['images']['tk_img'] = Image.open(BytesIO(b64decode(base64_encoded_string)))

    content_dict['images']['tk_img'] = content_dict['images']['tk_img'].resize((image_size, image_size),
                                                                               Image.ANTIALIAS)
    content_dict['images']['artwork'] = ImageTk.PhotoImage(content_dict['images']['tk_img'])

    content_dict['widgets']['artwork'].configure(image=content_dict['images']['artwork'])

    del payload['attributes']['artwork']

    for k, v in payload['attributes'].items():
        if k in content_dict['widgets']:
            content_dict['widgets'][k].config(text=unescape(v))
            if len(content_dict['widgets'][k]['text']) > CHAR_LIM:
                content_dict['widgets'][k]['text'] = ('  ' + content_dict['widgets'][k]['text'] + '  ') * 3

                hscroll_label(k)

    switch_on()


def hscroll_label(k):
    global content_dict

    content_dict['coords'][k]['x'] -= 2

    content_dict['coords'][k]['x'] = 0.5 * dims[0] \
        if content_dict['coords'][k]['x'] < (0.5 * dims[0]) - (content_dict['widgets'][k].winfo_width() / 3) \
        else content_dict['coords'][k]['x']

    content_dict['widgets'][k].place(**content_dict['coords'][k])

    if len(content_dict['widgets'][k]['text']) > CHAR_LIM:
        content_dict['widgets']['canvas'].after(10, hscroll_label, k)
    else:
        content_dict['coords'][k]['x'] = 0.5 * dims[0]
        content_dict['widgets'][k].place(**content_dict['coords'][k])


def execute_command(payload):
    command_dict = {
        'switch_on': switch_on,
        'switch_off': switch_off
    }

    if payload['attributes']['command'] in command_dict:
        command_dict[payload['attributes']['command']]()
    else:
        raise ValueError('Command not found')


def on_message(client, userdata, msg):
    try:
        payload = loads(msg.payload)

        assert 'type' in payload and 'attributes' in payload

        if payload['type'] == 'display':
            update_display(payload)
        elif payload['type'] == 'command':
            execute_command(payload)

    except Exception as e:
        print(format_exc())
        pb_notify(e.__repr__(), **PB_PARAMS)


def get_update():
    mqtt_client.publish('crt-pi/get-update', payload='get_update')


def setup_mqtt_client():
    def on_connect(client, *args):
        client.subscribe(MQTT_TOPIC)

    temp_client = Client()
    temp_client.username_pw_set(**MQTT_CREDS)
    temp_client.on_connect = on_connect
    temp_client.on_message = on_message
    temp_client.connect(MQTT_BROKER, 1883, 60)

    return temp_client


def initialize():
    global image_size, content_dict, dims

    switch_on()

    client = setup_mqtt_client()

    root = Tk()
    root.attributes('-fullscreen', True)
    root.configure(bg=BG_COLOR)

    dims = root.winfo_screenwidth(), root.winfo_screenheight()

    image_size = int(0.65 * dims[1])

    crt_font = Font(family='Courier New', size=int(0.05 * dims[1]))

    content_dict = {
        'images': {
            'tk_img': None,
            'artwork': ''
        },
        'widgets': {
            'canvas': Canvas(root, width=dims[0], height=dims[1], **STANDARD_ARGS)
        },
        'coords': {
            'media_title': {'x': 0.5 * dims[0], 'y': 0.8 * dims[1], 'anchor': CENTER},
            'media_artist': {'x': 0.5 * dims[0], 'y': 0.9 * dims[1], 'anchor': CENTER}
        }
    }
    content_dict['widgets']['canvas'].place(x=0, y=0, width=dims[0], height=dims[1])

    content_dict['widgets']['artwork'] = Label(
        content_dict['widgets']['canvas'],
        image='',
        **STANDARD_ARGS
    )

    content_dict['widgets']['media_title'] = Label(
        content_dict['widgets']['canvas'],
        text='',
        font=crt_font,
        fg='#ffffff',
        bg=BG_COLOR
    )

    content_dict['widgets']['media_artist'] = Label(
        content_dict['widgets']['canvas'],
        text='',
        font=crt_font,
        fg='#ffffff',
        bg=BG_COLOR
    )

    content_dict['widgets']['artwork'].place(x=0.5 * dims[0], y=(0.5 * image_size) + (0.075 * dims[1]), anchor=CENTER)
    content_dict['widgets']['media_title'].place(**content_dict['coords']['media_title'])
    content_dict['widgets']['media_artist'].place(**content_dict['coords']['media_artist'])

    return client, root


if __name__ == '__main__':
    mqtt_client, tk_root = initialize()
    mqtt_client.loop_start()
    tk_root.after(1000, func=get_update)
    tk_root.mainloop()
