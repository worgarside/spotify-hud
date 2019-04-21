from os import getenv
from pprint import pprint

from dotenv import load_dotenv
from requests import get
from json import JSONDecodeError

load_dotenv()

HASS_ENDPOINT = f"http://{getenv('HASS_HOST')}:{getenv('HASS_PORT')}/api/"
HEADERS = {
    'Authorization': f"Bearer {getenv('HASS_ACCESS_TOKEN')}",
    'Content-Type': 'application/json'
}

MEDIA_PLAYERS = [
    {'entity_id': 'media_player.all_speakers',
     'priority': 1},
    {'entity_id': 'media_player.hifi_system',
     'priority': 2},
    {'entity_id': 'media_player.bedroom_home_mini',
     'priority': 3},
    {'entity_id': 'media_player.study_home_mini',
     'priority': 3}
]


def get_now_playing():
    for player in MEDIA_PLAYERS:
        res = get(f"{HASS_ENDPOINT}states/{player['entity_id']}", headers=HEADERS)
        if res.status_code == 404:
            # TODO: append numbers (e.g. media_player.all_speakers_3)
            continue
        try:
            state = res.json()
            if not state['state'] == 'off':
                return state
        except JSONDecodeError:
            pass
            # TODO find out why?

    return False


def main():
    # res = get(f"{HASS_ENDPOINT}states/{MEDIA_PLAYERS[2]['entity_id']}", headers=HEADERS)

    # pprint(res.json())
    pprint(get_now_playing())


if __name__ == '__main__':
    main()
