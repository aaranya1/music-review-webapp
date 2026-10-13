"""
Refresh the most-listened artists on ListenBrainz.

  1. Fetch the sitewide top artists (ListenBrainz, by MBID).
  2. Add any that aren't in the DB as Artist rows (name/country from MusicBrainz).
  3. Seed release groups not yet in the DB (seed_artist_albums, mode='missing').
     Existing artists only get new releases; new or album-less artists get
     their full discography.
  4. For these artists' albums added by this run, plus their 2025+ albums with
     no tracklist: fill tracks, backfill missing durations, seed MB credits.
  5. Fetch images for target artists missing image_url/background_url.

Resumable: step 3 skips artists already stamped (last_seeded_at) since --since,
which defaults to the start of today in DB time. Re-running the same day
picks up where it left off.

Usage:
    python seeds/refresh_top_artists.py --dry-run
    python seeds/refresh_top_artists.py [--range this_year] [--count 200] [--since YYYY-MM-DD]
"""

import os
import sys
import time
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from app import app
from db import db
from models import Artist, Album, Track, album_artist
from services.musicbrainz import search_mb_rels
from services.spotify import get_artist_image as spotify_image
from services.fanart import get_artist_background, get_artist_thumb
from services.wikidata import get_artist_image as wiki_image
from seeds.seed import seed_artist_albums
from seeds.credits import seed_mb
from seeds.backfill_track_durations import _backfill_album

LB_URL = 'https://api.listenbrainz.org/1/stats/sitewide/artists'
USER_AGENT = os.getenv('MB_USER_AGENT', 'Groovelog/0.1')


def _arg(name, default):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def fetch_top_artists(stats_range, count):
    resp = requests.get(LB_URL, params={'range': stats_range, 'count': count},
                        headers={'User-Agent': USER_AGENT}, timeout=30)
    resp.raise_for_status()
    seen, out = set(), []
    for a in resp.json()['payload']['artists']:
        mbid = a.get('artist_mbid')
        # Entries without an MBID can't be matched reliably; skip duplicates too
        if mbid and mbid not in seen:
            seen.add(mbid)
            out.append({'mbid': mbid, 'name': a['artist_name'], 'listens': a['listen_count']})
    return out


def ensure_artists(targets, dry_run):
    existing = {a.mbid for a in Artist.query.filter(Artist.mbid.in_([t['mbid'] for t in targets]))}
    missing = [t for t in targets if t['mbid'] not in existing]
    print(f'{len(targets)} target artists: {len(existing)} in DB, {len(missing)} to add')
    if dry_run:
        for t in missing:
            print(f'  would add: {t["name"]}')
        return
    for i, t in enumerate(missing):
        data = search_mb_rels('artist', t['mbid'])
        name = (data or {}).get('name') or t['name']
        db.session.add(Artist(mbid=t['mbid'], name=name, country=(data or {}).get('country')))
        db.session.commit()
        print(f'  [{i+1}/{len(missing)}] + {name}')


def post_process_albums(target_mbids, run_started, dry_run):
    """Tracks, durations and credits for albums this run touched."""
    artist_ids = [a.id for a in Artist.query.filter(Artist.mbid.in_(target_mbids))]
    album_q = (Album.query.join(album_artist, album_artist.c.album_id == Album.id)
               .filter(album_artist.c.artist_id.in_(artist_ids)))
    new_albums = album_q.filter(Album.created_at >= run_started).distinct().all()
    empty_recent = (album_q.filter(Album.release_date >= datetime(2025, 1, 1))
                    .filter(~Album.tracks.any()).distinct().all())
    print(f'\nPost-processing: {len(new_albums)} albums added this run, '
          f'{len(empty_recent)} 2025+ albums without tracks')
    if dry_run:
        return

    # Tracklists for recent albums that had none (often announced-but-unreleased)
    filled = 0
    for album in empty_recent:
        data = search_mb_rels('release', album.mbid, inc='recordings')
        for disc in (data or {}).get('media', []):
            for t in disc.get('tracks', []):
                rec = t.get('recording', {})
                if rec.get('id') and Track.query.filter_by(album_id=album.id, mbid=rec['id']).first():
                    continue
                db.session.add(Track(mbid=rec.get('id'), title=t.get('title') or rec.get('title'),
                                     duration_ms=t.get('length'), track_number=t.get('position'),
                                     disc_number=disc.get('position', 1), album_id=album.id))
                filled += 1
        db.session.commit()
    print(f'  tracks added to previously empty albums: {filled}')

    touched = {a.id: a for a in new_albums + empty_recent}
    durations = 0
    for album in touched.values():
        if any(t.duration_ms is None and t.mbid for t in album.tracks):
            durations += _backfill_album(album)
    print(f'  durations backfilled: {durations}')

    for i, album_id in enumerate(touched):
        print(f'  credits [{i+1}/{len(touched)}]')
        seed_mb(album_id=album_id)


def fetch_images(target_mbids, dry_run):
    artists = (Artist.query.filter(Artist.mbid.in_(target_mbids))
               .filter((Artist.image_url.is_(None)) | (Artist.background_url.is_(None))).all())
    print(f'\nImages: {len(artists)} target artists missing image or background')
    if dry_run:
        return
    for i, artist in enumerate(artists):
        if not artist.image_url:
            try:
                thumb = spotify_image(artist.name)
            except Exception as e:  # Spotify credentials/API problems shouldn't stop the run
                print(f'  Spotify unavailable ({e}); falling back')
                thumb = None
            artist.image_url = thumb or get_artist_thumb(artist.mbid) or wiki_image(artist.name, size=500)
        if not artist.background_url:
            artist.background_url = get_artist_background(artist.mbid) or wiki_image(artist.name, size=1280)
        db.session.commit()
        print(f'  [{i+1}/{len(artists)}] {artist.name}: image {"✓" if artist.image_url else "✗"}, '
              f'background {"✓" if artist.background_url else "✗"}')


def main():
    dry_run = '--dry-run' in sys.argv
    stats_range = _arg('--range', 'this_year')
    count = int(_arg('--count', '200'))
    started = time.time()

    with app.app_context():
        run_started = db.session.execute(db.text('select now()::timestamp')).scalar()
        since = _arg('--since', None)
        skip_since = (datetime.strptime(since, '%Y-%m-%d') if since
                      else run_started.replace(hour=0, minute=0, second=0, microsecond=0))

        targets = fetch_top_artists(stats_range, count)
        print(f'ListenBrainz {stats_range} top {count}: {len(targets)} unique artists with MBIDs')
        print(f'Top 10: {", ".join(t["name"] for t in targets[:10])}\n')
        target_mbids = [t['mbid'] for t in targets]

        ensure_artists(targets, dry_run)

        if dry_run:
            done = Artist.query.filter(Artist.mbid.in_(target_mbids),
                                       Artist.last_seeded_at >= skip_since).count()
            print(f'\nAlbums: would process {len(targets) - done} artists '
                  f'({done} already seeded since {skip_since:%Y-%m-%d %H:%M} UTC)')
        else:
            print(f'\n── Seeding albums (skipping artists seeded since {skip_since:%Y-%m-%d %H:%M} UTC) ──')
            seed_artist_albums(mode='missing', artist_mbids=target_mbids, skip_seeded_since=skip_since)

    # seed_artist_albums manages its own app context; open a fresh one so we
    # see everything it committed
    with app.app_context():
        post_process_albums(target_mbids, run_started, dry_run)
        fetch_images(target_mbids, dry_run)

    print(f'\nDone in {(time.time() - started) / 60:.1f} min{" (dry run, nothing written)" if dry_run else ""}.')


if __name__ == '__main__':
    main()
