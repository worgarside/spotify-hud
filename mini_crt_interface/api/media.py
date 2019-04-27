from requests import get
from os import getenv
from bs4 import BeautifulSoup


def get_tv_metadata():
    return check_plex()


def check_plex():
    def get_tv_video():
        for video in videos:
            player = video.find('player').attrs
            if player['address'] == getenv('BRAVIA_IP_ADDRESS') \
                    or 'bravia' in player['device'].lower() \
                    or 'bravia' in player['title'].lower():
                attrs = video.attrs
                attrs['state'] = player['state']
                return attrs
        else:
            return {'error': 'No video playing', 'type': 'error'}

    try:
        plex_servers = [
            dict(
                zip(['host', 'port', 'x-plex-token'], server)
            ) for server in list(
                zip(
                    getenv('PLEX_HOSTS').split(),
                    getenv('PLEX_PORTS').split(),
                    getenv('X_PLEX_TOKENS').split()
                )
            )
        ]
    except AttributeError as e:
        return {
            'error': 'Unable to parse envfile',
            'data': {
                'message': str(e)
            },
            'type': 'error'
        }

    for server in plex_servers:
        res = get(
            f"http://{server['host']}:{server['port']}/status/sessions",
            headers={
                'X-Plex-Token': server['x-plex-token']
            },
            timeout=5
        )

        soup = BeautifulSoup(res.content.decode(), 'html.parser')
        videos = soup.findAll('video')
        tv_video = get_tv_video()

        if tv_video and 'error' not in tv_video:
            break
    else:
        return

    if tv_video['type'] == 'episode':
        metadata = {
            'show': tv_video['grandparenttitle'],
            'season': f"{int(tv_video['parentindex']):02d}",
            'episode': f"{int(tv_video['index']):02d}",
        }
    elif tv_video['type'] == 'movie':
        metadata = {
            'show': 'youtube',
            'season': f"{1:02d}",
            'episode': f"{3:02d}",
        }

    elif tv_video['type'] == 'error':
        return tv_video
    else:
        return {'error': 'Unknown video type', 'data': tv_video['type'], 'type': 'error'}

    metadata['X-Plex-Token'] = server['x-plex-token']
    metadata['art'] = f"http://{server['host']}:{server['port']}{tv_video['art']}?X-Plex-Token={server['x-plex-token']}"
    metadata['type'] = tv_video['type']
    metadata['title'] = tv_video['title']
    metadata['state'] = tv_video['state']

    return metadata


if __name__ == '__main__':
    from pprint import pprint
    from dotenv import load_dotenv

    load_dotenv()

    pprint(get_tv_metadata())