"""
Re-fetch tracklists for recent-year albums that currently have zero tracks.
These are usually new albums whose tracklists weren't announced at seed time
and have since been published on MusicBrainz.

Usage:
    python seeds/refresh_empty_2026.py               # defaults to 2025+
    python seeds/refresh_empty_2026.py --since 2024  # custom cutoff
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date
from app import app
from db import db
from models import Album, Track
from services.musicbrainz import search_mb_rels


def run(since_year=2025):
    with app.app_context():
        start = date(since_year, 1, 1)

        albums = (
            Album.query
            .filter(Album.release_date >= start)
            .filter(~Album.tracks.any())
            .filter(Album.mbid.isnot(None))
            .order_by(Album.release_date, Album.title)
            .all()
        )
        print(f'Found {len(albums)} albums from {since_year}+ with no tracks.\n')

        filled = 0
        still_empty = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else '?'
            print(f'[{i+1}/{len(albums)}] {album.title} — {artist_name} ({album.release_date})')

            release_data = search_mb_rels('release', album.mbid, inc='recordings')
            if not release_data:
                print('  ✗ No MB data, skipping.')
                still_empty += 1
                continue

            media = release_data.get('media', [])
            added = 0
            for disc in media:
                disc_number = disc.get('position', 1)
                for track in disc.get('tracks', []):
                    recording = track.get('recording', {})
                    mbid = recording.get('id')
                    title = track.get('title') or recording.get('title')

                    if mbid and Track.query.filter_by(album_id=album.id, mbid=mbid).first():
                        continue

                    db.session.add(Track(
                        mbid=mbid,
                        title=title,
                        duration_ms=track.get('length'),
                        track_number=track.get('position'),
                        disc_number=disc_number,
                        album_id=album.id,
                    ))
                    added += 1

            if added:
                db.session.commit()
                print(f'  ✓ Added {added} tracks.')
                filled += 1
            else:
                print('  — Still no tracks on MB.')
                still_empty += 1

        print(f'\nDone. Filled: {filled} | Still empty: {still_empty}')


if __name__ == '__main__':
    since = 2025
    if '--since' in sys.argv:
        idx = sys.argv.index('--since')
        since = int(sys.argv[idx + 1])
    run(since_year=since)
