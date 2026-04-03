import os
import requests
import time
from requests.exceptions import RequestException

BASE_URL = 'https://musicbrainz.org/ws/2'
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

def search_cover_art(id):
    global _last_request_time
    try:
        _rate_limit()
        url = f'https://coverartarchive.org/release-group/{id}/'
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException:
        return {}

def search_mb(type, query, limit=5, retries=3):
    global _last_request_time

    for attempt in range(retries):
        try:
            _rate_limit()

            params = {
                'query': f'{query}',
                'fmt': 'json',
                'limit': limit
            }

            if type == 'artist':
                url = f'{BASE_URL}/artist/'    
            elif type == 'release-group':
                url = f'{BASE_URL}/release-group/'
            elif type == 'release':
                url = f'{BASE_URL}/release/'
            elif type == 'recording':
                url = f'{BASE_URL}/recording/'
            else:
                raise ValueError("Invalid type. Must be 'artist', 'release-group', or 'release'.")
    
            response = requests.get(
                url,
                headers= HEADERS,
                params= params,
                timeout= 10
            )

            response.raise_for_status()

            _last_request_time = time.time()
            return response.json()
    
        except RequestException as e:
            print(f"Request failed (attempt {attempt+1}): {e}")
            time.sleep(2)
            
    print("All retry attempts failed.")
    return {}

def search_mb_rels(type, mbid, inc='url-rels', retries=3):
    global _last_request_time

    for attempt in range(retries):
        try:
            _rate_limit()

            params = {
                'inc': inc,
                'fmt': 'json'
            }

            if type == 'artist':
                url = f'{BASE_URL}/artist/{mbid}/'    
            elif type == 'release-group':
                url = f'{BASE_URL}/release-group/{mbid}/'
            elif type == 'release':
                url = f'{BASE_URL}/release/{mbid}/'
            elif type == 'recording':
                url = f'{BASE_URL}/recording/{mbid}/'
            else:
                raise ValueError("Invalid type. Must be 'artist', 'release-group', or 'release'.")
            
            response = requests.get(
                url,
                headers= HEADERS,
                params= params,
                timeout= 10
            )

            response.raise_for_status()

            _last_request_time = time.time()
            return response.json()

        except RequestException as e:
            print(f"Request failed (attempt {attempt+1}): {e}")
            time.sleep(2)

    print("All retry attempts failed.")
    return {}

def browse_releases(rg_mbid, retries=3):
    """
    Fetch all official releases in a release group via the browse API.
    Returns a list of release dicts with media/format info.
    """
    global _last_request_time
    offset = 0
    limit = 100
    all_releases = []

    while True:
        for attempt in range(retries):
            try:
                _rate_limit()
                params = {
                    'release-group': rg_mbid,
                    'status': 'official',
                    'inc': 'media+release-groups',
                    'fmt': 'json',
                    'limit': limit,
                    'offset': offset,
                }
                response = requests.get(
                    f'{BASE_URL}/release/',
                    headers=HEADERS,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                _last_request_time = time.time()
                data = response.json()
                releases = data.get('releases', [])
                all_releases.extend(releases)
                if offset + limit >= data.get('release-count', 0):
                    return all_releases
                offset += limit
                break
            except RequestException as e:
                print(f'  browse_releases attempt {attempt+1} failed: {e}')
                time.sleep(2)
        else:
            print('  browse_releases: all retries failed')
            return all_releases


def normalize_release(release):
    artist_credit = release.get('artist-credit', [])

    artists = []
    for credit in artist_credit:
        if 'artist' in credit:
            artists.append({
                'mbid': credit['artist'].get('id'),
                'name': credit['artist'].get('name')
            })

    date = (
        release.get('first-release-date') or
        release.get('release-group', {}).get('first-release-date')
        ) 

    year = None
    if date and date.strip() and len(date) >= 4:
        try:
            year = int(date[:4])
        except ValueError:
            year = None

    return {
        'mbid': release.get('id'),
        'title': release.get('title'),
        'artists': artists, 
        'release_date': year,
        'cover_url': release.get('cover_url')
    }