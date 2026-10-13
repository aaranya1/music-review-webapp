"""
Fill in missing track durations from sibling releases in the same release group.
Useful when the picked release omits track lengths (e.g. some digital releases),
but another release in the same group has them.

For each album with at least one null-duration track:
  - List sibling releases via browse_releases(release_group_mbid)
  - For each sibling, fetch its recordings and build {recording_mbid: length_ms}
  - Fill any matching null tracks; short-circuit once all are filled

Usage:
    python seeds/backfill_track_durations.py
    python seeds/backfill_track_durations.py --album-id 123   # single album
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from db import db
from models import Album, Track
from services.musicbrainz import browse_releases, search_mb_rels


def _durations_from_release(release_data):
    """Build {recording_mbid: length_ms} from a release's media."""
    out = {}
    for disc in release_data.get('media', []):
        for track in disc.get('tracks', []):
            rec = track.get('recording', {})
            mbid = rec.get('id')
            length = track.get('length') or rec.get('length')
            if mbid and length:
                out[mbid] = length
    return out


def _backfill_album(album):
    artist_name = album.artists[0].name if album.artists else '?'
    null_tracks = [t for t in album.tracks if t.duration_ms is None and t.mbid]

    if not null_tracks:
        return 0

    print(f'[{album.id}] {album.title} — {artist_name} '
          f'({len(null_tracks)} tracks missing duration)')

    rg_mbid = album.release_group_mbid
    if not rg_mbid:
        print('  ✗ No release_group_mbid, skipping.')
        return 0

    siblings = browse_releases(rg_mbid)
    sibling_mbids = [r.get('id') for r in siblings if r.get('id') and r.get('id') != album.mbid]
    if not sibling_mbids:
        print('  — No sibling releases to check.')
        return 0

    needed = {t.mbid: t for t in null_tracks}
    filled = 0

    for rel_mbid in sibling_mbids:
        if not needed:
            break
        data = search_mb_rels('release', rel_mbid, inc='recordings')
        if not data:
            continue
        durations = _durations_from_release(data)
        for mbid in list(needed.keys()):
            if mbid in durations:
                track = needed.pop(mbid)
                track.duration_ms = durations[mbid]
                print(f'  ✓ {track.title}: {durations[mbid]}ms (from {rel_mbid})')
                filled += 1

    if filled:
        db.session.commit()
    if needed:
        print(f'  — {len(needed)} track(s) still missing duration after all siblings.')

    return filled


def run(album_id=None):
    with app.app_context():
        if album_id:
            album = Album.query.get(album_id)
            if not album:
                print(f'No album with id={album_id}')
                return
            albums = [album]
        else:
            albums = (
                Album.query
                .join(Track)
                .filter(Track.duration_ms.is_(None), Track.mbid.isnot(None))
                .distinct()
                .order_by(Album.release_date.desc())
                .all()
            )

        print(f'Checking {len(albums)} album(s) for missing durations.\n')

        total_filled = 0
        for album in albums:
            total_filled += _backfill_album(album)

        print(f'\nDone. Filled {total_filled} durations.')


if __name__ == '__main__':
    album_id = None
    if '--album-id' in sys.argv:
        idx = sys.argv.index('--album-id')
        album_id = int(sys.argv[idx + 1])
    run(album_id=album_id)
