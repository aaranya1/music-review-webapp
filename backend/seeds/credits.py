"""
Credits seeder.

Modes:
  mb                   Seed credits from MusicBrainz (tracks with no credits)
  discogs              Seed credits from Discogs (albums with no credits, default)
  discogs --replace    Replace existing credits if Discogs has more per album
"""

import sys
import re
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app

_DISCOGS_SUFFIX_RE = re.compile(r'\s*\(\d+\)$')
from db import db
from models import Album, Track, Artist, Credit
from services.musicbrainz import search_mb_rels
from services.discogs import find_release, extract_track_credits, extract_tracklist, _title_similarity
from sqlalchemy.exc import IntegrityError


# ── MusicBrainz ────────────────────────────────────────────────────────────────

MB_CREDIT_ROLES = {
    "mix", "producer", "co-producer", "executive producer",
    "writer", "composer", "lyricist", "additional production",
    "additional", "programming", "instrument", "vocal"
}

ATTRIBUTE_EXPANDED_ROLES = {"instrument", "vocal"}


def _resolve_mb_role(rel):
    role = rel.get('type', '').lower()
    if role not in MB_CREDIT_ROLES:
        return []
    if role in ATTRIBUTE_EXPANDED_ROLES:
        attributes = rel.get('attributes', [])
        return [attr.lower() for attr in attributes] if attributes else [role]
    return [role]


MB_INC = (
    'recordings+artist-credits+artist-rels+'
    'recording-level-rels+work-rels+work-level-rels'
)


def _add_mb_credit(track, artist_data, role, seen):
    """Insert a Credit row if it doesn't already exist for (track, name, role).
    `seen` is a set of (track_id, name, role) tuples already handled this pass."""
    if not artist_data:
        return 0
    credited_name = artist_data.get('name')
    credited_mbid = artist_data.get('id')
    if not credited_name:
        return 0

    key = (track.id, credited_name, role)
    if key in seen:
        return 0
    seen.add(key)

    with db.session.no_autoflush:
        exists = Credit.query.filter_by(
            track_id=track.id,
            artist_name=credited_name,
            role=role,
        ).first()
        if exists:
            return 0

        artist_obj = Artist.query.filter_by(mbid=credited_mbid).first() if credited_mbid else None
        db.session.add(Credit(
            track_id=track.id,
            artist_id=artist_obj.id if artist_obj else None,
            artist_name=credited_name,
            role=role,
        ))
        return 1


def _process_recording_relations(track, relations, seen):
    """Walk a recording's relations. Handles both artist rels and work→artist rels."""
    added = 0
    for rel in relations:
        target_type = rel.get('target-type')

        if target_type == 'artist':
            # Recording-level artist credits: producer, mixer, engineer, etc.
            roles = _resolve_mb_role(rel)
            for role in roles:
                added += _add_mb_credit(track, rel.get('artist'), role, seen)

        elif target_type == 'work' and rel.get('type') == 'performance':
            # Drill into the work for composer / lyricist / arranger
            work = rel.get('work') or {}
            for wrel in work.get('relations', []):
                if wrel.get('target-type') != 'artist':
                    continue
                roles = _resolve_mb_role(wrel)
                for role in roles:
                    added += _add_mb_credit(track, wrel.get('artist'), role, seen)
    return added


def seed_mb(album_id=None):
    """
    Seed credits from MusicBrainz at the album level.
    One API request per album fetches all tracks' relations at once
    (recording-level + work-level).

    If album_id is provided, only that album is processed (ignores the
    "missing credits" filter — always re-fetches).
    """
    with app.app_context():
        if album_id:
            album = Album.query.get(album_id)
            if not album:
                print(f"No album with id={album_id}")
                return
            if not album.mbid:
                print(f"Album {album_id} has no mbid.")
                return
            albums = [album]
        else:
            albums = (
                Album.query
                .filter(Album.mbid.isnot(None))
                .filter(Album.tracks.any(
                    Track.mbid.isnot(None) & ~Track.credits.any()
                ))
                .order_by(Album.id)
                .all()
            )

        print(f"Found {len(albums)} albums with tracks missing credits.\n")

        total_added = 0
        total_albums_done = 0
        total_skipped = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else '?'
            print(f"[{i+1}/{len(albums)}] {album.title} — {artist_name}")

            data = search_mb_rels('release', album.mbid, inc=MB_INC)
            if not data:
                print("  ✗ No MB data, skipping.")
                total_skipped += 1
                continue

            # Build lookup maps from DB tracks
            by_mbid = {t.mbid: t for t in album.tracks if t.mbid}
            by_pos = {(t.disc_number, t.track_number): t for t in album.tracks}

            album_added = 0
            seen = set()
            for disc in data.get('media', []):
                disc_number = disc.get('position', 1)
                for entry in disc.get('tracks', []):
                    recording = entry.get('recording') or {}
                    rec_mbid = recording.get('id')
                    pos_key = (disc_number, entry.get('position'))

                    db_track = by_mbid.get(rec_mbid) or by_pos.get(pos_key)
                    if not db_track:
                        continue

                    relations = recording.get('relations', [])
                    if not relations:
                        continue

                    album_added += _process_recording_relations(db_track, relations, seen)

            try:
                db.session.commit()
                print(f"  ✓ Added {album_added} credits.")
                total_added += album_added
                total_albums_done += 1
            except IntegrityError:
                db.session.rollback()
                print("  ✗ IntegrityError on commit, rolled back.")
                total_skipped += 1

        print(f"\nMB credits complete. "
              f"Albums processed: {total_albums_done} | Credits added: {total_added} | Skipped: {total_skipped}")


# ── Discogs ────────────────────────────────────────────────────────────────────

def _count_track_credits(album):
    return sum(len(t.credits) for t in album.tracks)


def _match_discogs_track(discogs_track, db_tracks):
    position = discogs_track.get('position', '').strip()
    title = discogs_track.get('title', '').strip()

    track_num = None
    if position.isdigit():
        track_num = int(position)
    else:
        match = re.match(r'^[A-Za-z](\d+)$', position)
        if match:
            track_num = int(match.group(1))

    if track_num:
        for t in db_tracks:
            if t.track_number == track_num:
                return t

    best_score, best_track = 0.0, None
    for t in db_tracks:
        score = _title_similarity(title, t.title)
        if score > best_score:
            best_score, best_track = score, t

    return best_track if best_score >= 0.8 else None


def _update_track_duration(db_track, discogs_track, changed_count):
    duration = discogs_track.get('duration_ms')
    if duration and db_track.duration_ms:
        if abs(duration - db_track.duration_ms) > 2000:
            db_track.duration_ms = duration
            return changed_count + 1
    elif duration and not db_track.duration_ms:
        db_track.duration_ms = duration
        return changed_count + 1
    return changed_count


def _write_discogs_credits(album, discogs_credits_by_position, db_tracks):
    added = 0
    for discogs_pos, credits in discogs_credits_by_position.items():
        db_track = _match_discogs_track({'position': discogs_pos, 'title': ''}, db_tracks)
        if not db_track:
            continue

        with db.session.no_autoflush:
            Credit.query.filter_by(track_id=db_track.id).delete()

            seen = set()
            for credit_data in credits:
                name = _DISCOGS_SUFFIX_RE.sub('', credit_data['artist_name']).strip()
                role = credit_data['role']
                key = (name, role)
                if key in seen:
                    continue
                seen.add(key)

                artist_obj = Artist.query.filter(Artist.name.ilike(name)).first()
                db.session.add(Credit(
                    track_id=db_track.id,
                    artist_id=artist_obj.id if artist_obj else None,
                    artist_name=name,
                    role=role,
                    source='discogs',
                ))
                added += 1
    return added


def seed_discogs(mode='missing'):
    """
    Seed credits from Discogs.
    mode='missing'  — only albums with zero credits
    mode='replace'  — all albums, replace MB if Discogs has more
    """
    with app.app_context():
        if mode == 'missing':
            albums = (
                Album.query
                .filter(~Album.tracks.any(Track.credits.any()))
                .order_by(Album.title)
                .all()
            )
            print(f"Mode: missing only — {len(albums)} albums with no credits\n")
        else:
            albums = Album.query.order_by(Album.title).all()
            print(f"Mode: replace if more — {len(albums)} total albums\n")

        total_albums_updated = 0
        total_credits_added = 0
        total_tracks_updated = 0
        total_no_match = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else ''
            print(f"[{i+1}/{len(albums)}] {album.title} — {artist_name}")

            db_tracks = list(album.tracks)
            if not db_tracks:
                print(f"  No tracks in DB, skipping.")
                continue

            if album.discogs_id:
                from services.discogs import get_release
                release = get_release(album.discogs_id)
                print(f"  Using cached Discogs ID: {album.discogs_id}")
            else:
                release = find_release(album.title, artist_name, len(db_tracks))
                if release:
                    album.discogs_id = release.get('id')
                    db.session.flush()

            if not release:
                print(f"  No Discogs match found")
                total_no_match += 1
                continue

            print(f"  Matched: \"{release.get('title')}\" (ID: {release.get('id')})")

            discogs_credits = extract_track_credits(release)
            discogs_tracklist = extract_tracklist(release)

            tracks_changed = 0
            for dt in discogs_tracklist:
                db_track = _match_discogs_track(dt, db_tracks)
                if db_track:
                    tracks_changed = _update_track_duration(db_track, dt, tracks_changed)

            if tracks_changed:
                print(f"  ~ Updated {tracks_changed} track duration(s)")
                total_tracks_updated += tracks_changed

            if not discogs_credits:
                print(f"  No per-track credits on Discogs")
                db.session.commit()
                continue

            discogs_credit_count = sum(len(v) for v in discogs_credits.values())

            if mode == 'replace':
                existing_count = _count_track_credits(album)
                if existing_count >= discogs_credit_count:
                    print(f"  Existing credits ({existing_count}) >= Discogs ({discogs_credit_count}), skipping")
                    db.session.commit()
                    continue

            added = _write_discogs_credits(album, discogs_credits, db_tracks)

            try:
                db.session.commit()
                print(f"  Added {added} credits")
                total_albums_updated += 1
                total_credits_added += added
            except IntegrityError:
                db.session.rollback()
                print(f"  Integrity error on commit, rolled back")

        print(f"\n── Summary ───────────────────────────────────────")
        print(f"Albums updated:   {total_albums_updated}")
        print(f"Credits added:    {total_credits_added}")
        print(f"Tracks updated:   {total_tracks_updated}")
        print(f"No Discogs match: {total_no_match}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'discogs'

    album_id = None
    if '--album-id' in sys.argv:
        idx = sys.argv.index('--album-id')
        album_id = int(sys.argv[idx + 1])

    if mode == 'mb':
        seed_mb(album_id=album_id)
    elif mode == 'discogs':
        replace = '--replace' in sys.argv
        seed_discogs('replace' if replace else 'missing')
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python seeds/credits.py [mb [--album-id N] | discogs [--replace]]")
