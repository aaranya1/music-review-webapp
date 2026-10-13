"""
One-time script to fill release_group_mbid for albums where it is NULL.
Fetches each release from MusicBrainz using the existing album.mbid
and extracts the release-group id from the response.

Usage:
    python seeds/fix_missing_rg_mbids.py
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from db import db
from models import Album
from services.musicbrainz import search_mb_rels


def run():
    with app.app_context():
        albums = (
            Album.query
            .filter(Album.release_group_mbid.is_(None))
            .filter(Album.mbid.isnot(None))
            .order_by(Album.id)
            .all()
        )
        total = len(albums)
        print(f'Found {total} albums missing release_group_mbid.\n')

        fixed = 0
        failed = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else ''
            print(f'[{i+1}/{total}] {album.title} — {artist_name}')

            data = search_mb_rels('release', album.mbid, inc='release-groups')
            if not data:
                print(f'  ✗ No MB response, skipping.')
                failed += 1
                continue

            rg_mbid = data.get('release-group', {}).get('id')
            if not rg_mbid:
                print(f'  ✗ No release-group in response, skipping.')
                failed += 1
                continue

            album.release_group_mbid = rg_mbid
            db.session.commit()
            print(f'  ✓ release_group_mbid: {rg_mbid}')
            fixed += 1

        print(f'\nDone. Fixed: {fixed} | Still missing: {failed}')


if __name__ == '__main__':
    run()
