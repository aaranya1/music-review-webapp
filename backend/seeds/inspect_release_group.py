"""
Inspect all releases in a MusicBrainz release group and show the signals the
picker uses. Useful for diagnosing bad picks (SWAG-style bundles, stub releases,
missing tracklists) and for choosing a pin manually.

Usage:
    python seeds/inspect_release_group.py <release_group_mbid>
    python seeds/inspect_release_group.py --album-id 42
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from models import Album
from services.musicbrainz import browse_releases
from seeds.seed import _pick_best_release, _total_tracks, _is_bundle_title


def _formats(release):
    return ', '.join(
        m.get('format') or '?' for m in release.get('media', [])
    ) or '?'


def _disambig(release):
    bits = []
    if release.get('disambiguation'):
        bits.append(release['disambiguation'])
    for m in release.get('media', []):
        if m.get('disambiguation'):
            bits.append(m['disambiguation'])
    return '; '.join(bits)


def inspect(rg_mbid, rg_title=None):
    with app.app_context():
        releases = browse_releases(rg_mbid)
        if not releases:
            print(f'No releases found for {rg_mbid}.')
            return

        print(f'Release group: {rg_mbid}')
        if rg_title:
            print(f'Title: {rg_title}')
        print(f'{len(releases)} release(s) returned by MB.\n')

        best = _pick_best_release(releases, rg_mbid=rg_mbid, rg_title=rg_title)
        best_id = best.get('id') if best else None

        # Sort: winner first, then by date
        releases_sorted = sorted(
            releases,
            key=lambda r: (r.get('id') != best_id, r.get('date') or '9999'),
        )

        header = f"{'★':<2} {'MBID':<38} {'Date':<12} {'C':<3} {'#T':<4} {'Format':<20} {'Title'}"
        print(header)
        print('-' * len(header))

        for r in releases_sorted:
            star = '★' if r.get('id') == best_id else ''
            title = r.get('title', '')
            date = r.get('date') or '-'
            country = r.get('country') or '-'
            track_count = _total_tracks(r)
            fmt = _formats(r)
            flags = []
            if rg_title and _is_bundle_title(title, rg_title):
                flags.append('BUNDLE')
            disambig = _disambig(r)
            if disambig:
                flags.append(disambig)

            suffix = f'  [{", ".join(flags)}]' if flags else ''
            print(f'{star:<2} {r.get("id"):<38} {date:<12} {country:<3} '
                  f'{track_count:<4} {fmt:<20} {title}{suffix}')

        print()
        if best:
            print(f'Picker choice: {best.get("id")}  —  "{best.get("title")}"')
            print(f'To pin manually: python seeds/pin_release.py <album_id> <release_mbid>')
        else:
            print('Picker: no candidate survived the filters.')


if __name__ == '__main__':
    if '--album-id' in sys.argv:
        idx = sys.argv.index('--album-id')
        album_id = int(sys.argv[idx + 1])
        with app.app_context():
            album = Album.query.get(album_id)
            if not album:
                print(f'No album with id={album_id}')
                sys.exit(1)
            if not album.release_group_mbid:
                print(f'Album {album_id} has no release_group_mbid.')
                sys.exit(1)
            print(f'Album: [{album.id}] {album.title} (mbid={album.mbid}, rg={album.release_group_mbid})')
            if album.pinned_release_mbid:
                print(f'Pinned to: {album.pinned_release_mbid}')
            print()
            inspect(album.release_group_mbid, rg_title=album.title)
    elif len(sys.argv) >= 2 and not sys.argv[1].startswith('--'):
        inspect(sys.argv[1])
    else:
        print(__doc__)
