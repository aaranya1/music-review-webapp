"""
Delete pre-cutoff albums with fewer than N tracks.
These are almost always stubs, compilations missing data, or bad MB matches.

Usage:
    python seeds/cleanup_sparse_albums.py                              # dry run, defaults (before 2026, <3 tracks)
    python seeds/cleanup_sparse_albums.py --apply                      # actually delete
    python seeds/cleanup_sparse_albums.py --before 2025 --min-tracks 1 # pre-2025 albums with 0 tracks
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date
from app import app
from db import db
from models import Album, Track
from sqlalchemy import func


def run(before_year=2026, min_tracks=3, apply=False):
    with app.app_context():
        cutoff = date(before_year, 1, 1)

        track_count = (
            db.session.query(Track.album_id, func.count(Track.id).label('n'))
            .group_by(Track.album_id)
            .subquery()
        )

        albums = (
            Album.query
            .outerjoin(track_count, track_count.c.album_id == Album.id)
            .filter(Album.release_date < cutoff)
            .filter(func.coalesce(track_count.c.n, 0) < min_tracks)
            .order_by(Album.release_date, Album.title)
            .all()
        )

        print(f'Found {len(albums)} pre-{before_year} albums with <{min_tracks} tracks.\n')

        for album in albums:
            artist_name = album.artists[0].name if album.artists else '?'
            print(f'  [{album.release_date}] {album.title} — {artist_name} '
                  f'({len(album.tracks)} tracks)')

        if not apply:
            print('\nDry run. Pass --apply to delete.')
            return

        for album in albums:
            db.session.delete(album)
        db.session.commit()
        print(f'\nDeleted {len(albums)} albums.')


def _arg(name, default, cast=int):
    if name in sys.argv:
        idx = sys.argv.index(name)
        return cast(sys.argv[idx + 1])
    return default


if __name__ == '__main__':
    run(
        before_year=_arg('--before', 2026),
        min_tracks=_arg('--min-tracks', 3),
        apply='--apply' in sys.argv,
    )
