import os
import time
import requests
from requests.exceptions import RequestException

BASE_URL = 'https://webservice.fanart.tv/v3/music'

_last_request_time = 0


def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 0.5:
        time.sleep(0.5 - elapsed)
    _last_request_time = time.time()


def _fetch(mbid, retries=3):
    """Fetch the full Fanart.tv artist payload by MBID, or None."""
    api_key = os.getenv('FANART_API_KEY')
    if not api_key:
        return None

    for attempt in range(retries):
        try:
            _rate_limit()
            response = requests.get(
                f'{BASE_URL}/{mbid}',
                params={'api_key': api_key},
                timeout=10,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            print(f'  Fanart.tv request failed (attempt {attempt + 1}): {e}')
            time.sleep(2)

    return None


def get_artist_background(mbid):
    """
    Return the top-liked artistbackground URL for an artist by MBID, or None.
    artistbackground images are 1920×1080.
    """
    data = _fetch(mbid)
    if not data:
        return None
    images = data.get('artistbackground', [])
    return images[0].get('url') if images else None


def get_artist_thumb(mbid):
    """
    Return the top-liked artistthumb URL for an artist by MBID, or None.
    artistthumb images are 1000×1000 square.
    """
    data = _fetch(mbid)
    if not data:
        return None
    images = data.get('artistthumb', [])
    return images[0].get('url') if images else None
