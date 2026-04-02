import os
import requests
import time
from requests.exceptions import RequestException

BASE_URL = 'https://en.wikipedia.org/w/api.php'
HEADERS = {
    'User-Agent': os.getenv('MB_USER_AGENT', 'MusicApp/1.0')
}

_last_request_time = 0


def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 1:
        time.sleep(1 - elapsed)
    _last_request_time = time.time()


def _fetch(name, size, retries=3):
    """Raw Wikipedia pageimages API call. Returns parsed JSON or {}."""
    for attempt in range(retries):
        try:
            _rate_limit()
            response = requests.get(
                BASE_URL,
                headers=HEADERS,
                params={
                    'action':      'query',
                    'titles':      name,
                    'prop':        'pageimages',
                    'pithumbsize': size,
                    'format':      'json',
                },
                timeout=10,
            )
            response.raise_for_status()
            _last_request_time = time.time()
            return response.json()
        except RequestException as e:
            print(f'  Wikidata request failed (attempt {attempt + 1}): {e}')
            time.sleep(2)

    print('  All Wikidata retry attempts failed.')
    return {}


def get_artist_image(name, size=500):
    """
    Return a Wikipedia thumbnail URL for the given artist name, or None.

    Args:
        name: artist name to search
        size: requested thumbnail width in pixels (actual may vary)
    """
    data  = _fetch(name, size)
    pages = data.get('query', {}).get('pages', {})
    if not pages:
        return None
    page = next(iter(pages.values()))
    return page.get('thumbnail', {}).get('source')
