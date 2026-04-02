"""
Updates artist images in one pass per artist.

  image_url      — Spotify → Fanart.tv artistthumb → Wikidata fallback
  background_url — Fanart.tv artistbackground → Wikidata fallback

Run with no flags to update all artists, or pass --missing to skip artists
that already have both fields populated.
"""

import sys
from app import app
from db import db
from models import Artist
from services.spotify import get_artist_image as spotify_image
from services.fanart import get_artist_background, get_artist_thumb
from services.wikidata import get_artist_image as wiki_image


def update_artist_images(missing_only=False, skip_spotify=False):
    with app.app_context():
        if missing_only:
            artists = Artist.query.filter(
                (Artist.image_url == None) | (Artist.background_url == None)
            ).order_by(Artist.name).all()
            print(f'Mode: missing only — {len(artists)} artist(s) with incomplete images\n')
        else:
            artists = Artist.query.order_by(Artist.name).all()
            print(f'Mode: all — {len(artists)} artist(s)\n')

        if skip_spotify:
            print('Spotify disabled — thumb will use Wikidata only\n')

        updated_thumb      = 0
        updated_background = 0
        failed_thumb       = 0
        failed_background  = 0

        for i, artist in enumerate(artists):
            print(f'[{i + 1}/{len(artists)}] {artist.name}')

            # ── Thumb (image_url): Spotify → Fanart.tv thumb → Wikidata ──
            if not missing_only or not artist.image_url:
                thumb = None
                if not skip_spotify:
                    thumb = spotify_image(artist.name)
                    if not thumb:
                        print(f'  thumb: Spotify miss, trying Fanart.tv...')
                if not thumb:
                    thumb = get_artist_thumb(artist.mbid)
                    if not thumb:
                        print(f'  thumb: Fanart.tv miss, trying Wikidata...')
                        thumb = wiki_image(artist.name, size=500)

                if thumb:
                    artist.image_url = thumb
                    print(f'  thumb: ✓')
                    updated_thumb += 1
                else:
                    print(f'  thumb: ✗ not found')
                    failed_thumb += 1

            # ── Background (background_url): Fanart.tv → Wikidata ─────────
            if not missing_only or not artist.background_url:
                background = get_artist_background(artist.mbid)
                if not background:
                    print(f'  background: Fanart.tv miss, trying Wikidata...')
                    background = wiki_image(artist.name, size=1280)

                if background:
                    artist.background_url = background
                    print(f'  background: ✓')
                    updated_background += 1
                else:
                    print(f'  background: ✗ not found')
                    failed_background += 1

            db.session.commit()

        print(f'\n── Summary ──────────────────────────────────────')
        print(f'Thumb updated:       {updated_thumb}')
        print(f'Thumb failed:        {failed_thumb}')
        print(f'Background updated:  {updated_background}')
        print(f'Background failed:   {failed_background}')


if __name__ == '__main__':
    missing_only  = '--missing'       in sys.argv
    skip_spotify  = '--skip-spotify'  in sys.argv
    update_artist_images(missing_only=missing_only, skip_spotify=skip_spotify)
