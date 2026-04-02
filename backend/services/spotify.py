import os
import time
import requests
from requests.exceptions import RequestException

TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE  = 'https://api.spotify.com/v1'

_token = None
_token_expiry = 0


def _get_token():
    """Fetch or refresh the client credentials access token."""
    global _token, _token_expiry

    if _token and time.time() < _token_expiry - 60:
        return _token

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

    if not client_id or not client_secret:
        raise RuntimeError('SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env')

    response = requests.post(
        TOKEN_URL,
        data={'grant_type': 'client_credentials'},
        auth=(client_id, client_secret),
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    _token = data['access_token']
    _token_expiry = time.time() + data['expires_in']
    return _token


def _headers():
    return {'Authorization': f'Bearer {_get_token()}'}


def _get(url, params=None, retries=3):
    """GET with retry and 429 backoff.

    Rate-limit retries are handled separately from error retries so that
    repeated 429 responses don't exhaust the error budget.
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=_headers(), params=params, timeout=10)

            # Drain rate-limit responses before checking for real errors
            for _ in range(10):
                if response.status_code != 429:
                    break
                raw_wait = int(response.headers.get('Retry-After', '5'))
                # Spotify sometimes returns a Unix timestamp instead of seconds
                wait = raw_wait if raw_wait <= 300 else 5
                print(f'  Rate limited, waiting {wait}s...')
                time.sleep(wait)
                response = requests.get(url, headers=_headers(), params=params, timeout=10)

            response.raise_for_status()
            time.sleep(0.3)
            return response.json()

        except RequestException as e:
            print(f'  Request failed (attempt {attempt + 1}): {e}')
            time.sleep(2)

    print('  All retry attempts failed.')
    return {}


# ── Artist ──────────────────────────────────────────────────────────────────

def search_artist(name):
    """
    Search for an artist by name.
    Returns the raw Spotify artist object for the best match, or None.
    """
    data = _get(f'{API_BASE}/search', params={
        'q':     name,
        'type':  'artist',
        'limit': 5
    })

    items = data.get('artists', {}).get('items', [])
    if not items:
        return None

    # Prefer exact name match (case-insensitive), fall back to top result
    name_lower = name.lower().strip()
    for item in items:
        if item.get('name', '').lower().strip() == name_lower:
            return item

    return items[0]


def get_artist_image(name):
    """
    Return the best available image URL for an artist, or None.
    Prefers the largest image Spotify provides.
    """
    artist = search_artist(name)
    if not artist:
        return None

    images = artist.get('images', [])
    if not images:
        return None

    # Spotify returns images sorted largest first
    # Pick the largest that's at least 300px wide, otherwise take what we get
    for img in images:
        if img.get('width', 0) >= 300:
            return img['url']

    return images[0]['url']


# ── Album ────────────────────────────────────────────────────────────────────

def search_album(title, artist_name):
    """
    Search for an album by title and artist.
    Returns the raw Spotify album object for the best match, or None.
    """
    query = f'album:{title} artist:{artist_name}'
    data  = _get(f'{API_BASE}/search', params={
        'q': query,
        'type': 'album',
        'limit': 5
    })

    items = data.get('albums', {}).get('items', [])
    if not items:
        return None

    title_lower = title.lower().strip()
    for item in items:
        if item.get('name', '').lower().strip() == title_lower:
            return item

    return items[0]


def get_album_cover(title, artist_name, min_size=500):
    """
    Return the best available cover URL for an album, or None.
    Prefers images at least min_size px wide.
    """
    album = search_album(title, artist_name)
    if not album:
        return None

    images = album.get('images', [])
    if not images:
        return None

    for img in images:
        if img.get('width', 0) >= min_size:
            return img['url']

    return images[0]['url']