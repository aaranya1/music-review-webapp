"""
Pin an album to a specific MusicBrainz release MBID and re-seed it.
Use this when the picker chose the wrong release for a release group
(e.g., a bundled sibling, a deluxe edition, a wrong-disc-count release).

The pin persists via Album.pinned_release_mbid, so future re-seeds respect it
and don't silently undo the correction.

Usage:
    python seeds/pin_release.py <album_id> <release_mbid>
    python seeds/pin_release.py --unpin <album_id>
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from db import db
from models import Album, Track, track_artist
from services.musicbrainz import search_mb_rels
from seeds.seed import _process_release_group


def pin(album_id, release_mbid):
    with app.app_context():
        album = Album.query.get(album_id)
        if not album:
            print(f'No album with id={album_id}')
            return

        print(f'Album: [{album.id}] {album.title} (current mbid={album.mbid})')

        # Resolve release → release-group so we can route through _process_release_group
        data = search_mb_rels('release', release_mbid, inc='release-groups')
        if not data:
            print(f'✗ Could not fetch release {release_mbid} from MB.')
            return
        rg_mbid = data.get('release-group', {}).get('id')
        if not rg_mbid:
            print(f'✗ Release {release_mbid} has no release-group on MB.')
            return

        # Wipe existing tracks — the pinned release has a different layout.
        # Clear track_artist first via raw SQL to avoid ORM bookkeeping drift
        # on the Track.artists secondary (no cascade defined).
        track_ids = [t.id for t in album.tracks]
        track_count = len(track_ids)
        if track_ids:
            db.session.execute(
                track_artist.delete().where(track_artist.c.track_id.in_(track_ids))
            )
            db.session.flush()
            for t in list(album.tracks):
                db.session.delete(t)
            db.session.flush()
        print(f'  Wiped {track_count} existing tracks')

        album.pinned_release_mbid = release_mbid
        album.release_group_mbid = rg_mbid
        db.session.flush()

        _process_release_group(
            rg_mbid=rg_mbid,
            rg_title=album.title,
            artist_objs=list(album.artists),
            artist_cache={},
            mode='reseed',
            existing_album=album,
        )
        db.session.commit()
        print('\nDone.')


def unpin(album_id):
    with app.app_context():
        album = Album.query.get(album_id)
        if not album:
            print(f'No album with id={album_id}')
            return
        if not album.pinned_release_mbid:
            print(f'Album [{album.id}] {album.title} is not pinned.')
            return
        print(f'Unpinning album [{album.id}] {album.title} (was pinned to {album.pinned_release_mbid})')
        album.pinned_release_mbid = None
        db.session.commit()


if __name__ == '__main__':
    if '--unpin' in sys.argv:
        idx = sys.argv.index('--unpin')
        unpin(int(sys.argv[idx + 1]))
    elif len(sys.argv) >= 3:
        pin(int(sys.argv[1]), sys.argv[2])
    else:
        print(__doc__)
