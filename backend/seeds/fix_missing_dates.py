"""
One-time script to fill release_date for albums where it is NULL.

Strategy per album (tries each in order until a date is found):
  1. release_group_mbid is set → browse all releases in that RG, pick earliest date
  2. album.mbid is set → fetch the release directly and read its date
  3. Search MB by title + primary artist name as a last resort

Usage:
    python seeds/fix_missing_dates.py
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from db import db
from models import Album
from services.musicbrainz import search_mb_rels, browse_releases, search_mb
from datetime import date


def _parse_date(date_str):
    if not date_str or not date_str.strip():
        return None
    parts = date_str.strip().split('-')
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def _date_from_rg(rg_mbid):
    """Browse releases in the release group, return earliest valid date."""
    releases = browse_releases(rg_mbid)
    dates = []
    for r in releases:
        d = _parse_date(r.get('date') or r.get('first-release-date', ''))
        if d:
            dates.append(d)
    return min(dates) if dates else None


def _date_from_release(release_mbid):
    """Fetch the release directly and read its date."""
    data = search_mb_rels('release', release_mbid, inc='release-groups')
    if not data:
        return None
    d = _parse_date(
        data.get('date') or
        data.get('release-group', {}).get('first-release-date', '')
    )
    return d


def _date_from_search(title, artist_name):
    """Search MB for the release group by title + artist, return first-release-date."""
    query = f'releasegroup:"{title}" AND artist:"{artist_name}"'
    result = search_mb('release-group', query, limit=1)
    rgs = result.get('release-groups', [])
    if not rgs:
        return None
    return _parse_date(rgs[0].get('first-release-date', ''))


def run():
    with app.app_context():
        albums = Album.query.filter(Album.release_date.is_(None)).order_by(Album.id).all()
        total = len(albums)
        print(f'Found {total} albums with missing release_date.\n')

        fixed = 0
        failed = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else ''
            print(f'[{i+1}/{total}] {album.title} — {artist_name}')

            release_date = None

            # 1. Try release group browse
            if album.release_group_mbid:
                release_date = _date_from_rg(album.release_group_mbid)
                if release_date:
                    print(f'  ✓ From RG browse: {release_date}')

            # 2. Try fetching release directly
            if not release_date and album.mbid:
                release_date = _date_from_release(album.mbid)
                if release_date:
                    print(f'  ✓ From release lookup: {release_date}')

            # 3. Search by title + artist
            if not release_date and artist_name:
                release_date = _date_from_search(album.title, artist_name)
                if release_date:
                    print(f'  ✓ From MB search: {release_date}')

            if release_date:
                album.release_date = release_date
                db.session.commit()
                fixed += 1
            else:
                print(f'  ✗ Could not find date, skipping.')
                failed += 1

        print(f'\nDone. Fixed: {fixed} | Still missing: {failed}')


if __name__ == '__main__':
    run()
