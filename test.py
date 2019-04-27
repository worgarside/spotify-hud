def test_gpio():
    from pigpio import pi as rasp_pi, OUTPUT
    from time import sleep

    PIN = 18
    DELAY = 4

    pi = rasp_pi()
    pi.set_mode(PIN, OUTPUT)

    pi.write(PIN, False)
    print('Off')
    sleep(DELAY)
    pi.write(PIN, True)
    print('On')
    sleep(DELAY)
    pi.write(PIN, False)
    print('Off')
    sleep(DELAY)
    pi.write(PIN, True)
    print('On')
    sleep(DELAY)
    pi.write(PIN, False)
    print('Off')
    sleep(2)

    pi.stop()


def test_api():
    from requests import get
    from dotenv import load_dotenv
    from os import getenv
    from pprint import pprint

    load_dotenv()

    hass_endpoint = f"http://{getenv('HASS_HOST')}:{getenv('HASS_PORT')}/api"

    headers = {
        'Authorization': f"Bearer {getenv('HASS_ACCESS_TOKEN')}"
    }

    res = get(f'{hass_endpoint}/states', headers=headers)

    print(res.status_code, res.reason)

    media_players = [entity['entity_id'] for entity in res.json() if
                     entity['entity_id'].split('.')[0] == 'media_player']

    pprint(media_players)

    res = get(f'{hass_endpoint}/states/media_player.sony_bravia_tv', headers=headers)

    print(res.status_code, res.reason)

    pprint(res.json())


def test_plex():
    from requests import get
    from dotenv import load_dotenv
    from os import getenv
    from bs4 import BeautifulSoup

    load_dotenv()

    def get_tv_video():
        for video in videos:
            player = video.find('player').attrs
            if player['address'] == getenv('BRAVIA_IP_ADDRESS') \
                    or 'bravia' in player['device'].lower() \
                    or 'bravia' in player['title'].lower():
                return video.attrs
        else:
            return  # TODO?

    x_plex_token = getenv('X_PLEX_TOKEN')

    res = get(
        f"http://{getenv('PLEX_HOST')}:{getenv('PLEX_PORT')}/status/sessions",
        headers={
            'X-Plex-Token': x_plex_token
        }
    )

    if not res.status_code == 200:
        return  # TODO?

    soup = BeautifulSoup(res.content.decode(), 'html.parser')

    print(soup)
    return
    videos = soup.findAll('video')

    tv_video = get_tv_video()

    if not tv_video:
        return  # TODO?

    if tv_video['type'] == 'episode':
        metadata = {
            'title': tv_video['grandparenttitle'],
            'season': tv_video['parentindex'],
            'episode': tv_video['index'],
        }
    elif tv_video['type'] == 'movie':
        metadata = {
            'title': tv_video['title'],
            'season': None,
            'episode': None,
        }
    else:
        return  # TODO? wrong video type

    metadata['X-Plex-Token'] = x_plex_token
    metadata['art'] = tv_video['art']
    metadata['type'] = tv_video['type']

    print(metadata)


if __name__ == '__main__':
    test_plex()

# ?X-Plex-Token=w7qvD6mCFpvYStUjT7yE
