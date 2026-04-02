import os
import re
import time
import requests
from requests.exceptions import RequestException

API_BASE = 'https://api.discogs.com'

_last_request_time = 0
RATE_LIMIT_DELAY   = 1.1  # Discogs allows ~60/min, 1.1s keeps us safe


def _rate_limit():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    _last_request_time = time.time()


def _headers():
    token = os.getenv('DISCOGS_TOKEN')
    if not token:
        raise RuntimeError('DISCOGS_TOKEN must be set in .env')
    return {
        'Authorization': f'Discogs token={token}',
        'User-Agent':    os.getenv('MB_USER_AGENT', 'MusicApp/1.0'),
        'Accept':        'application/vnd.discogs.v2.discogs+json',
    }


def _get(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            _rate_limit()
            response = requests.get(url, headers=_headers(), params=params, timeout=10)

            if response.status_code == 429:
                wait = int(response.headers.get('Retry-After', 60))
                if wait > 300:
                    wait = 60
                print(f'  Rate limited, waiting {wait}s...')
                time.sleep(wait)
                continue

            if response.status_code == 404:
                return {}

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            print(f'  Request failed (attempt {attempt + 1}): {e}')
            time.sleep(2)

    print('  All retry attempts failed.')
    return {}


# ── Normalisation helpers ──────────────────────────────────────────────────

# Roles Discogs uses that we care about, normalised to our internal names
ROLE_MAP = {
    'producer':          'producer',
    'co-producer':       'co-producer',
    'executive producer':'executive producer',
    'produced by':       'producer',
    'written-by':        'writer',
    'written by':        'writer',
    'words by':          'lyricist',
    'lyrics by':         'lyricist',
    'music by':          'composer',
    'composed by':       'composer',
    'arranged by':       'arranger',
    'mixed by':          'mix',
    'mastered by':       'mastering',
    'programmed by':     'programming',
    'drums':             'drums',
    'bass':              'bass',
    'guitar':            'guitar',
    'keyboards':         'keyboards',
    'piano':             'piano',
    'synthesizer':       'synthesizer',
    'vocals':            'vocals',
    'backing vocals':    'backing vocals',
    'lead vocals':       'lead vocals',
    'saxophone':         'saxophone',
    'trumpet':           'trumpet',
    'strings':           'strings',
    'violin':            'violin',
    'cello':             'cello',
}

def _normalise_role(raw_role):
    """
    Parse a Discogs role string into a list of normalised role strings.
    Input:  "Producer, Written-By"
    Output: ['producer', 'writer']

    Handles:
    - Comma-separated multiple roles
    - Bracket annotations like "Guitar [Lead]" → 'guitar'
    - Case insensitivity
    """
    # Strip bracket annotations: "Guitar [Lead, Rhythm]" → "Guitar"
    raw_role = re.sub(r'\[.*?\]', '', raw_role)

    parts   = [p.strip().lower() for p in raw_role.split(',')]
    results = []

    for part in parts:
        part = part.strip(' -')
        if not part:
            continue
        normalised = ROLE_MAP.get(part)
        if normalised:
            results.append(normalised)

    return results


def _title_similarity(a, b):
    """Simple normalised similarity — strip punctuation, lowercase, compare."""
    def clean(s):
        return re.sub(r'[^a-z0-9 ]', '', s.lower().strip())
    a, b = clean(a), clean(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # Word overlap ratio
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    overlap  = len(words_a & words_b)
    return overlap / max(len(words_a), len(words_b))


# ── Search ────────────────────────────────────────────────────────────────

PREFERRED_FORMATS = {'digital', 'cd', 'file', 'mp3', 'flac', 'vinyl'}

def find_release(album_title, artist_name, expected_track_count=None):
    """
    Search Discogs for a release matching album_title + artist_name.
    Returns the best-matching release dict, or None.

    Strategy:
    1. Search by title + artist
    2. Filter to releases with similarity >= 0.8
    3. Prefer digital/CD formats
    4. Among remaining, prefer the one whose track count is closest
       to expected_track_count (if provided), else pick highest track count
    """
    data = _get(f'{API_BASE}/database/search', params={
        'release_title': album_title,
        'artist':        artist_name,
        'type':          'release',
        'per_page':      10,
    })

    results = data.get('results', [])
    if not results:
        return None

    candidates = []
    for r in results:
        title      = r.get('title', '')
        # Discogs search title format is "Artist - Album Title"
        # Strip the artist prefix if present
        if ' - ' in title:
            title = title.split(' - ', 1)[1]

        similarity = _title_similarity(album_title, title)
        if similarity < 0.8:
            continue

        formats = [f.get('name', '').lower() for f in r.get('formats', [])]
        is_preferred = any(f in PREFERRED_FORMATS for f in formats)

        candidates.append({
            'id':           r.get('id'),
            'title':        title,
            'similarity':   similarity,
            'is_preferred': is_preferred,
            'formats':      formats,
        })

    if not candidates:
        return None

    # Sort: preferred format first, then by similarity desc
    candidates.sort(key=lambda c: (not c['is_preferred'], -c['similarity']))

    # If we have an expected track count, fetch the top few and pick closest
    if expected_track_count and len(candidates) > 1:
        best     = None
        best_diff = float('inf')

        for candidate in candidates[:3]:
            release = get_release(candidate['id'])
            if not release:
                continue
            tracks = _extract_flat_tracklist(release.get('tracklist', []))
            diff   = abs(len(tracks) - expected_track_count)
            if diff < best_diff:
                best_diff = diff
                best      = release
            if diff == 0:
                break  # exact match, stop looking

        return best

    # Otherwise just fetch the top candidate
    return get_release(candidates[0]['id'])


def get_release(release_id):
    """Fetch a full release by Discogs release ID."""
    return _get(f'{API_BASE}/releases/{release_id}')


# ── Credits extraction ─────────────────────────────────────────────────────

def extract_track_credits(release):
    """
    Extract per-track credits from a Discogs release dict.

    Returns a dict keyed by track position string (e.g. "A1", "1", "2"):
    {
        "1": [
            {"artist_name": "Pharrell Williams", "role": "producer"},
            {"artist_name": "Pharrell Williams", "role": "writer"},
        ],
        ...
    }

    Only includes tracks that have their own extraartists.
    Album-level credits (release['extraartists']) are intentionally excluded
    per the design decision to only store per-track credits.
    """
    tracklist = release.get('tracklist', [])
    result    = {}

    for track in tracklist:
        position     = track.get('position', '').strip()
        extraartists = track.get('extraartists', [])

        if not position or not extraartists:
            continue

        credits = []
        for ea in extraartists:
            name     = ea.get('name', '').strip()
            raw_role = ea.get('role', '').strip()

            if not name or not raw_role:
                continue

            roles = _normalise_role(raw_role)
            for role in roles:
                credits.append({
                    'artist_name': name,
                    'role':        role,
                })

        if credits:
            result[position] = credits

    return result


# ── Tracklist extraction ───────────────────────────────────────────────────

def _extract_flat_tracklist(tracklist):
    """
    Flatten a Discogs tracklist (which may contain heading rows) into
    a list of real tracks only.
    """
    tracks = []
    for t in tracklist:
        # Skip headings and index tracks (position is blank or type_ is 'heading')
        if t.get('type_') == 'heading':
            continue
        position = t.get('position', '').strip()
        if not position:
            continue
        tracks.append(t)
    return tracks


def extract_tracklist(release):
    """
    Extract a normalised tracklist from a Discogs release.

    Returns a list of dicts:
    [
        {
            "position":    "1",          # Discogs position string
            "title":       "Track Name",
            "duration_ms": 245000,       # None if not available
        },
        ...
    ]
    """
    raw     = release.get('tracklist', [])
    flat    = _extract_flat_tracklist(raw)
    results = []

    for t in flat:
        position = t.get('position', '').strip()
        title    = t.get('title', '').strip()
        duration = t.get('duration', '').strip()  # format: "3:45" or ""

        duration_ms = None
        if duration:
            try:
                parts = duration.split(':')
                if len(parts) == 2:
                    duration_ms = (int(parts[0]) * 60 + int(parts[1])) * 1000
                elif len(parts) == 3:
                    duration_ms = (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
            except ValueError:
                pass

        results.append({
            'position':    position,
            'title':       title,
            'duration_ms': duration_ms,
        })

    return results