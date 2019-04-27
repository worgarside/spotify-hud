from requests import get
from os import getenv
from bs4 import BeautifulSoup


def get_tv_metadata():
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

    x_plex_token = getenv('X_PLEX_TOKEN')

    res = get(
        f"http://{getenv('PLEX_HOST')}:{getenv('PLEX_PORT')}/status/sessions",
        headers={
            'X-Plex-Token': x_plex_token
        },
        timeout=5
    )

    if not res.status_code == 200:
        return {
            'error': 'Invalid response code from Plex API',
            'data': {
                'status_code': res.status_code,
                'reason': res.reason
            },
            'type': 'error'
        }

    soup = BeautifulSoup(res.content.decode(), 'html.parser')

    videos = soup.findAll('video')

    tv_video = get_tv_video()

    if not tv_video:
        return {'error': 'No video playing', 'type': 'error'}

    if tv_video['type'] == 'episode':
        metadata = {
            'show': tv_video['grandparenttitle'],
            'season': tv_video['parentindex'],
            'episode': tv_video['index'],
        }
    elif tv_video['type'] == 'movie':
        metadata = {
            'season': None,
            'episode': None,
        }

    elif tv_video['type'] == 'error':
        return tv_video
    else:
        return {'error': 'Unknown video type', 'data': tv_video['type'], 'type': 'error'}

    metadata['X-Plex-Token'] = x_plex_token
    metadata['art'] = f"http://{getenv('PLEX_HOST')}:{getenv('PLEX_PORT')}{tv_video['art']}?X-Plex-Token={x_plex_token}"
    metadata['type'] = tv_video['type']
    metadata['title'] = tv_video['title']
    metadata['state'] = tv_video['state']

    return metadata
