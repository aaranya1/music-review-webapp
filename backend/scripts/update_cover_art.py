import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app
from db import db
from models import Album
from services.spotify import get_album_cover
import requests
import sys

HEADERS = {'User-Agent': 'MusicApp/1.0'}


def verify_url(url, timeout=6):
    try:
        r = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def caa_url(mbid, size=500):
    return f'https://coverartarchive.org/release/{mbid}/front-{size}.jpg'


def is_spotify_url(url):
    return url and 'i.scdn.co' in url


def update_cover_art(force=False, spotify_only=False, upgrade=False):
    """
    Args:
        force:        Update all albums regardless of current cover_url.
        spotify_only: Skip Cover Art Archive fallback.
        upgrade:      Target albums that have a cover_url but it's not a
                      Spotify URL — try to upgrade them to Spotify, keep
                      existing URL if Spotify search fails.
    """
    with app.app_context():
        if force:
            albums = Album.query.order_by(Album.title).all()
        elif upgrade:
            albums = (
                Album.query
                .filter(Album.cover_url.isnot(None))
                .filter(~Album.cover_url.like('%i.scdn.co%'))
                .order_by(Album.title)
                .all()
            )
        else:
            albums = (
                Album.query
                .filter(Album.cover_url.is_(None))
                .order_by(Album.title)
                .all()
            )

        total = len(albums)
        mode = 'upgrade' if upgrade else ('force' if force else 'missing only')
        print(f'Updating covers for {total} albums [{mode}]...\n')

        updated_spotify = 0
        updated_caa = 0
        kept_existing = 0
        failed = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else ''
            print(f'[{i + 1}/{total}] {album.title} — {artist_name}')

            # ── Try Spotify first ──────────────────────────────────────────
            url = get_album_cover(album.title, artist_name)

            if url:
                album.cover_url = url
                db.session.commit()
                print(f'  ✓ Spotify')
                updated_spotify += 1
                continue

            # ── In upgrade mode, keep the existing URL if Spotify fails ───
            if upgrade:
                print(f'  ~ Spotify not found, keeping existing URL')
                kept_existing += 1
                continue

            # ── Fall back to Cover Art Archive ─────────────────────────────
            if not spotify_only and album.mbid:
                caa_500 = caa_url(album.mbid, 500)
                caa_250 = caa_url(album.mbid, 250)

                if verify_url(caa_500):
                    album.cover_url = caa_500
                    db.session.commit()
                    print(f'  ~ CAA 500px fallback')
                    updated_caa += 1
                    continue

                if verify_url(caa_250):
                    album.cover_url = caa_250
                    db.session.commit()
                    print(f'  ~ CAA 250px fallback')
                    updated_caa += 1
                    continue

            print(f'  ✗ No cover found')
            failed += 1

        print(f'\nDone.')
        print(f'  Spotify:          {updated_spotify}')
        if upgrade:
            print(f'  Kept existing:    {kept_existing}')
        else:
            print(f'  Cover Art Archive:{updated_caa}')
            print(f'  Failed:           {failed}')


if __name__ == '__main__':
    force = '--force' in sys.argv
    spotify_only = '--spotify-only' in sys.argv
    upgrade = '--upgrade' in sys.argv
    update_cover_art(force=force, spotify_only=spotify_only, upgrade=upgrade)
