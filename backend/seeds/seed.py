import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app
from db import db
from models import Album, Artist, Track
from services.musicbrainz import search_mb, search_cover_art, normalize_release, search_mb_rels, browse_releases
import requests
import time
import re
import colorsys
from io import BytesIO
from PIL import Image
from datetime import date
from collections import Counter

HEADERS = {
    'User-Agent': os.getenv('MB_USER_AGENT', 'MusicApp/1.0')
}

SECONDARY_TYPE_BLOCKLIST = {
    "live", "compilation", "dj-mix", "spokenword",
    "remix", "interview", "soundtrack", "mixtape/street"
}

FORMAT_PRIORITY = ['Digital Media', 'CD', 'Vinyl', 'Cassette']

# ── Artists to seed ────────────────────────────────────────────────────────────

NEW_ARTISTS = [
    # Rock / Alt
    "Radiohead",
    "Tame Impala",
    "The Strokes",
    "Arctic Monkeys",
    "Vampire Weekend",
    "Frank Ocean",
    "LCD Soundsystem",
    "Bloc Party",
    "The National",
    "Interpol",
    "Yeah Yeah Yeahs",
    "MGMT",
    "Phoenix",
    "Foals",
    "Alt-J",
    "Hozier",
    "Florence and the Machine",
    "Bon Iver",
    "Sufjan Stevens",

    # Hip-hop / R&B
    "Tyler, the Creator",
    "Childish Gambino",
    "Anderson .Paak",
    "Kendrick Lamar",
    "J. Cole",
    "Isaiah Rashad",
    "ScHoolboy Q",
    "Vince Staples",
    "Run the Jewels",
    "Joey Bada$$",
    "Freddie Gibbs",
    "Denzel Curry",
    "JID",
    "Baby Keem",
    "Doechii",
    "Brent Faiyaz",
    "Lucky Daye",
    "6LACK",
    "Daniel Caesar",
    "H.E.R.",

    # Pop
    "Charli XCX",
    "Gracie Abrams",
    "Olivia Rodrigo",
    "Conan Gray",
    "beabadoobee",
    "girl in red",
    "Clairo",
    "Phoebe Bridgers",
    "boygenius",
    "Soccer Mommy",
    "Mitski",
    "Japanese Breakfast",
    "Caroline Polachek",
    "Rina Sawayama",
    "Kim Petras",
    "Troye Sivan",
    "years & years",
    "Sigrid",
    "Ava Max",
    "Anne-Marie",

    # Electronic / Dance
    "Four Tet",
    "Jamie xx",
    "Caribou",
    "Fred again..",
    "Bicep",
    "Jon Hopkins",
    "Bonobo",
    "Disclosure",
    "Jungle",
    "Parcels",
    "Nils Frahm",

    # Latin
    "Myke Towers",
    "Sech",
    "Jhay Cortez",
    "Anuel AA",
    "Lunay",
    "Mora",
    "Bad Gyal",
    "Rosalía",

    # Global / Other
    "Burna Boy",
    "WizKid",
    "Tems",
    "Fireboy DML",
    "Rema",
    "Omah Lay",
    "Ckay",
    "Yemi Alade",
    "Anitta",
    "Ludmilla",
]

ARTISTS_BY_FRIENDS = [
    "Good Kid", "TWRP", "My Chemical Romance", "Pierce the Veil", "Waterparks",
    "Laufey", "Mitski", "Panchiko", "Gloc-9", "Eraserheads", "Asin", "MF DOOM",
    "Queen", "Green Day", "Panic! At The Disco", "BINI", "Red Velvet", "Le Sserafim",
    "Fleetwood Mac", "OutKast", "Skindred", "System of a Down", "Iron Maiden",
    "Metallica", "Megadeth", "Black Sabbath", "Judas Priest", "Paramore",
    "Hozier", "Kate Bush", "Bowling for Soup", "Elliott Smith", "The Cure",
    "Hail the Sun", "Machine Girl", "Nick Drake", "Linkin Park", "Imagine Dragons",
    "Avicii", "Twenty One Pilots", "Falling in Reverse", "Lady Gaga", "Fall Out Boy",
    "Porter Robinson", "Red Hot Chili Peppers", "Halsey", "Doja Cat", "Slipknot",
    "Rage Against the Machine", "Three Days Grace", "Mumford & Sons", "Olivia Rodrigo",
    "Jon Bellion", "Sabrina Carpenter", "Ado", "Fujii Kaze", "Måneskin", "Muse",
    "One Direction", "The Smiths", "ABBA", "Glass Animals", "Dean Martin",
]

MISC_ARTISTS = [
    "Elliott Smith", "beabadoobee", "The 1975", "Tom Odell", "Kodaline",
    "Oklou", "Joji", "Dijon", "Geese", "Sam Gellaitry", "Poets of the Fall",
    "Gesaffelstein", "St. Vincent", "Yebba", "Majid Jordan", "Mark Ronson",
    "Amy Winehouse", "U2", "KAYTRANADA", "Justice",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def verify_cover_url(url, timeout=6):
    try:
        r = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def get_cover_url(rg_mbid):
    cover_json = search_cover_art(rg_mbid)
    images = cover_json.get('images', [])
    if not images:
        return None

    first_image = images[0]
    image_url = first_image.get('image', '')
    thumbnails = first_image.get('thumbnails', {})
    cover_url = (
        thumbnails.get('500') or
        thumbnails.get('large') or
        thumbnails.get('250') or
        image_url
    )

    if cover_url and not verify_cover_url(cover_url):
        return None

    return cover_url


def _parse_date(date_str):
    """
    Parse a MusicBrainz date string into a Python date object.
    Handles YYYY, YYYY-MM, YYYY-MM-DD. Returns None if unparseable.
    """
    if not date_str or not date_str.strip():
        return None
    parts = date_str.strip().split('-')
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def _total_tracks(release):
    """Sum track counts across all media in a release."""
    return sum(
        m.get('track-count', 0)
        for m in release.get('media', [])
    )


def _pick_best_release(releases):
    """
    Apply the release selection algorithm:
    1. Filter to Digital Media format; fall back to CD, then any format
    2. Filter out releases with no country code
    3. Most frequent release date; earliest on tie
    4. Most frequent track count; lowest on tie
    5. Prefer XW region (soft)
    6. Prefer explicit (soft)
    Returns the best release dict, or None if no candidates.
    """
    if not releases:
        return None

    # Step 1: Format filter with fallback chain
    candidates = None
    for fmt in FORMAT_PRIORITY:
        filtered = [
            r for r in releases
            if any(m.get('format') == fmt for m in r.get('media', []))
        ]
        if filtered:
            candidates = filtered
            break
    if not candidates:
        candidates = releases

    # Step 2: Must have country code
    with_country = [r for r in candidates if r.get('country')]
    if with_country:
        candidates = with_country

    # Step 3: Most frequent release date
    dates = [r.get('date', '') for r in candidates]
    date_counts = Counter(d for d in dates if d)
    if date_counts:
        top_count = max(date_counts.values())
        top_dates = {d for d, c in date_counts.items() if c == top_count}
        # Earliest on tie
        best_date = min(top_dates)
        candidates = [r for r in candidates if r.get('date', '') == best_date]

    # Step 4: Most frequent track count; lowest on tie
    track_counts = [_total_tracks(r) for r in candidates]
    count_freq = Counter(tc for tc in track_counts if tc > 0)
    if count_freq:
        top_freq = max(count_freq.values())
        top_tcs = {tc for tc, f in count_freq.items() if f == top_freq}
        best_tc = min(top_tcs)
        candidates = [r for r in candidates if _total_tracks(r) == best_tc]

    # Step 5: Prefer XW region (soft)
    xw = [r for r in candidates if r.get('country') == 'XW']
    if xw:
        candidates = xw

    # Step 6: Prefer explicit (soft)
    explicit = [
        r for r in candidates
        if any(
            m.get('disambiguation', '').lower() == 'explicit'
            or r.get('disambiguation', '').lower() == 'explicit'
            for m in r.get('media', [])
        )
    ]
    if explicit:
        candidates = explicit

    return candidates[0]


def _get_or_create_artist_by_mbid(mbid, name, artist_cache):
    """Get or create an Artist record, using cache to avoid redundant queries."""
    if not mbid:
        return None
    if mbid in artist_cache:
        return artist_cache[mbid]
    artist_obj = Artist.query.filter_by(mbid=mbid).first()
    if not artist_obj:
        artist_obj = Artist(mbid=mbid, name=name)
        db.session.add(artist_obj)
        print(f'  + New artist: {name}')
    artist_cache[mbid] = artist_obj
    return artist_obj


def _seed_tracks(album, release_data):
    """
    Seed tracks from a release's media. Returns count of new tracks added.
    Skips tracks whose recording MBID already exists globally.
    """
    added = 0
    for disc in release_data.get('media', []):
        disc_number = disc.get('position', 1)
        for track in disc.get('tracks', []):
            recording = track.get('recording', {})
            mbid = recording.get('id')
            title = track.get('title') or recording.get('title')
            if mbid and Track.query.filter_by(mbid=mbid).first():
                continue
            db.session.add(Track(
                mbid=mbid,
                title=title,
                duration_ms=track.get('length'),
                track_number=track.get('position'),
                disc_number=disc_number,
                album_id=album.id
            ))
            added += 1
    return added


def _process_release_group(rg_mbid, rg_title, artist_objs, artist_cache, mode='missing'):
    """
    Fetch all releases for a release group, apply selection algorithm,
    upsert the album record, seed tracks, enrich feat titles.

    mode:
      'missing' — skip if album with this rg_mbid already exists
      'force'   — update existing album if found
      'reseed'  — same as force, used for existing-album re-seeding
    """
    # Check existing by release group MBID
    existing = Album.query.filter_by(release_group_mbid=rg_mbid).first()
    if existing and mode == 'missing':
        print(f'  Already seeded: {existing.title}, skipping.')
        return

    # Fetch all official releases in this release group
    releases = browse_releases(rg_mbid)
    if not releases:
        print(f'  No releases found for "{rg_title}", skipping.')
        return

    best = _pick_best_release(releases)
    if not best:
        print(f'  Could not pick best release for "{rg_title}", skipping.')
        return

    release_mbid = best.get('id')
    title = best.get('title', rg_title)
    release_date = _parse_date(best.get('date') or best.get('first-release-date', ''))

    if not release_mbid:
        print(f'  No MBID on best release for "{rg_title}", skipping.')
        return

    if not release_date:
        print(f'  No valid date for "{title}", skipping.')
        return

    # Fetch full release data with recordings
    release_data = search_mb_rels('release', release_mbid, inc='recordings+artist-credits')
    if not release_data:
        print(f'  Could not fetch full release data for "{title}", skipping.')
        return

    # Cover art
    cover_url = get_cover_url(rg_mbid)

    # Upsert album
    album = existing or Album.query.filter_by(mbid=release_mbid).first()
    if album:
        old_mbid = album.mbid
        album.mbid = release_mbid
        album.release_group_mbid = rg_mbid
        album.title = title
        album.release_date = release_date
        if cover_url:
            album.cover_url = cover_url
        if old_mbid != release_mbid:
            print(f'  MBID: {old_mbid} → {release_mbid}')
    else:
        album = Album(
            mbid=release_mbid,
            release_group_mbid=rg_mbid,
            title=title,
            release_date=release_date,
            cover_url=cover_url
        )
        db.session.add(album)

    # Update artist credits
    if artist_objs:
        album.artists = artist_objs
    else:
        # Pull from release artist-credit if no explicit artist_objs passed
        for credit in best.get('artist-credit', []):
            if 'artist' not in credit:
                continue
            a = credit['artist']
            artist_obj = _get_or_create_artist_by_mbid(a.get('id'), a.get('name', ''), artist_cache)
            if artist_obj and artist_obj not in album.artists:
                album.artists.append(artist_obj)

    db.session.flush()

    # Seed tracks
    track_count = _seed_tracks(album, release_data)

    # Enrich feat titles
    t_updated, a_linked, _, _ = _enrich_feat_titles_for_album(album, release_data=release_data)

    try:
        db.session.commit()
        print(
            f'  ✓ {title} ({release_date.year}) — '
            f'{track_count} tracks added | {t_updated} titles enriched | '
            f'{a_linked} artists linked | cover: {"✓" if cover_url else "✗"}'
        )
    except Exception as e:
        db.session.rollback()
        print(f'  ✗ Commit failed for "{title}": {e}')


def _get_valid_release_groups(artist_mbid, include_eps=True):
    """Fetch and filter release groups for an artist."""
    rg_base = f'arid:{artist_mbid} AND status:official'

    album_rgs = search_mb(
        'release-group',
        f'{rg_base} AND primarytype:album',
        limit=100
    ).get('release-groups', [])

    ep_rgs = []
    if include_eps:
        ep_rgs = search_mb(
            'release-group',
            f'{rg_base} AND primarytype:ep',
            limit=50
        ).get('release-groups', [])

    def _filter(rgs):
        valid = []
        for rg in rgs:
            secondary = [t.lower() for t in rg.get('secondary-types', [])]
            if any(t in SECONDARY_TYPE_BLOCKLIST for t in secondary):
                continue
            valid.append(rg)
        return sorted(valid, key=lambda x: x.get('first-release-date', ''), reverse=True)

    return _filter(album_rgs), _filter(ep_rgs)


# ── Seeding modes ──────────────────────────────────────────────────────────────

def reseed_existing_albums():
    """
    Re-seed all albums already in the DB using the new algorithm.
    Updates MBID, release_group_mbid, release_date, tracks, feat titles.
    """
    with app.app_context():
        albums = Album.query.order_by(Album.id).all()
        print(f'Re-seeding {len(albums)} existing albums...\n')
        artist_cache = {}

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else '?'
            print(f'[{i+1}/{len(albums)}] {album.title} — {artist_name}')

            # If we already have a release_group_mbid, use it directly
            if album.release_group_mbid:
                rg_mbid = album.release_group_mbid
            else:
                # Derive release group from the existing release MBID
                release_data = search_mb_rels('release', album.mbid, inc='release-groups')
                if not release_data:
                    print(f'  ✗ No MB data, skipping')
                    continue
                rg_mbid = release_data.get('release-group', {}).get('id')
                if not rg_mbid:
                    print(f'  ✗ No release group found, skipping')
                    continue

            _process_release_group(
                rg_mbid=rg_mbid,
                rg_title=album.title,
                artist_objs=list(album.artists),
                artist_cache=artist_cache,
                mode='reseed'
            )

        print('\nReseed complete.')


def seed_artist_albums(mode='missing', artist_names=None):
    """
    Seed albums for artists already in the DB.

    mode='missing' — only release groups not yet in DB
    mode='force'   — process all release groups, update existing
    artist_names   — optional list to restrict to specific artists by name
    """
    with app.app_context():
        query = Artist.query.order_by(Artist.name)
        if artist_names:
            query = query.filter(Artist.name.in_(artist_names))
        artists = query.all()

        print(f'Processing {len(artists)} artists [{mode}]...\n')
        artist_cache = {a.mbid: a for a in artists}

        for i, artist in enumerate(artists):
            print(f'\n── [{i+1}/{len(artists)}] {artist.name} ──')
            album_rgs, ep_rgs = _get_valid_release_groups(artist.mbid)
            all_rgs = album_rgs + ep_rgs
            print(f'  {len(album_rgs)} albums, {len(ep_rgs)} EPs in release groups')

            for rg in all_rgs:
                rg_mbid = rg.get('id')
                rg_title = rg.get('title', '')
                print(f'  → {rg_title}')
                _process_release_group(
                    rg_mbid=rg_mbid,
                    rg_title=rg_title,
                    artist_objs=[artist],
                    artist_cache=artist_cache,
                    mode=mode
                )

        print('\nDone.')


def seed_new_artists(artist_names=None):
    """
    Seed new artists and their full discographies from scratch.
    Skips artists already in the DB. Creates new artist records as encountered.
    """
    if artist_names is None:
        artist_names = NEW_ARTISTS

    with app.app_context():
        artist_cache = {}

        for artist_name in artist_names:
            print(f'\n── {artist_name} ──')

            # Skip if already in DB
            existing_artist = Artist.query.filter(Artist.name.ilike(artist_name)).first()
            if existing_artist:
                print(f'  Already in DB, skipping.')
                continue

            # Find artist MBID
            result = search_mb('artist', artist_name, 1)
            mb_artists = result.get('artists', [])
            if not mb_artists:
                print(f'  Could not find on MusicBrainz, skipping.')
                continue

            mb_artist = mb_artists[0]
            artist_mbid = mb_artist.get('id')
            artist_obj = Artist(mbid=artist_mbid, name=mb_artist.get('name', artist_name))
            db.session.add(artist_obj)
            db.session.flush()
            artist_cache[artist_mbid] = artist_obj
            print(f'  Created: {artist_obj.name} [{artist_mbid}]')

            album_rgs, ep_rgs = _get_valid_release_groups(artist_mbid)
            all_rgs = album_rgs + ep_rgs
            print(f'  {len(album_rgs)} albums, {len(ep_rgs)} EPs')

            for rg in all_rgs:
                rg_mbid = rg.get('id')
                rg_title = rg.get('title', '')
                print(f'  → {rg_title}')
                _process_release_group(
                    rg_mbid=rg_mbid,
                    rg_title=rg_title,
                    artist_objs=[artist_obj],
                    artist_cache=artist_cache,
                    mode='missing'
                )

        print('\nNew artist seeding complete.')


# ── Cover art updater ──────────────────────────────────────────────────────────

def update_cover_art(force=False):
    """
    Update cover URLs for albums missing them (or all albums if force=True).
    Constructs the URL directly from the release MBID — no API call needed.
    Verifies each URL with a HEAD request before saving.
    """
    with app.app_context():
        query = Album.query if force else Album.query.filter(Album.cover_url.is_(None))
        albums = query.all()
        print(f"Updating covers for {len(albums)} albums.")

        updated = 0
        failed = 0
        for album in albums:
            url = f"https://coverartarchive.org/release/{album.mbid}/front-500.jpg"
            if verify_cover_url(url):
                album.cover_url = url
                print(f"  ✓ {album.title}")
                updated += 1
            else:
                url_250 = f"https://coverartarchive.org/release/{album.mbid}/front-250.jpg"
                if verify_cover_url(url_250):
                    album.cover_url = url_250
                    print(f"  ~ {album.title} (250px fallback)")
                    updated += 1
                else:
                    print(f"  ✗ {album.title} — no cover found")
                    failed += 1

        db.session.commit()
        print(f"\nCover art update complete. Updated: {updated}, Failed: {failed}")


# ── Featured artist title restoration ─────────────────────────────────────────

FEAT_JOIN_RE = re.compile(r'\b(feat\.?|ft\.?|featuring|with)\b', re.IGNORECASE)


def _parse_artist_credits(artist_credits, album_artist_mbids):
    suffix_parts = []
    extra_artists = []
    for i, credit in enumerate(artist_credits):
        if i == 0:
            continue
        artist = credit.get('artist', {})
        mbid = artist.get('id')
        name = artist.get('name', '').strip()
        join = artist_credits[i - 1].get('joinphrase', '')
        if not name:
            continue
        if mbid not in album_artist_mbids:
            extra_artists.append({'mbid': mbid, 'name': name})
        if FEAT_JOIN_RE.search(join):
            suffix_parts.append((join.strip(), name))
    return suffix_parts, extra_artists


def _build_suffix(suffix_parts):
    if not suffix_parts:
        return None
    keyword = suffix_parts[0][0]
    names = [suffix_parts[0][1]]
    for join, name in suffix_parts[1:]:
        names.append(f'{join} {name}'.strip())
    return f'({keyword} {", ".join(names)})'


def _get_or_create_artist(mbid, name):
    artist = Artist.query.filter_by(mbid=mbid).first()
    if not artist:
        artist = Artist(mbid=mbid, name=name)
        db.session.add(artist)
        db.session.flush()
        return artist, True
    return artist, False


def _enrich_feat_titles_for_album(album, release_data=None):
    """
    Enrich track titles with feat. suffixes and link featured artists
    for a single album. Fetches MB data if not provided.
    Returns (titles_updated, artists_linked, artists_created, skipped).
    """
    album_artist_mbids = {a.mbid for a in album.artists}

    if release_data is None:
        release_data = search_mb_rels('release', album.mbid, inc='recordings+artist-credits')
    if not release_data:
        return 0, 0, 0, 1

    enrichment = {}
    for disc in release_data.get('media', []):
        for track in disc.get('tracks', []):
            mb_title = track.get('title', '').strip()
            recording = track.get('recording', {})
            recording_mbid = recording.get('id')
            credits = recording.get('artist-credit', [])
            if not recording_mbid or len(credits) <= 1:
                continue
            suffix_parts, extra_artists = _parse_artist_credits(credits, album_artist_mbids)
            enrichment[recording_mbid] = {
                'mb_title': mb_title,
                'suffix_parts': suffix_parts,
                'extra_artists': extra_artists,
            }

    if not enrichment:
        return 0, 0, 0, 0

    titles_updated = artists_linked = artists_created = 0

    for db_track in album.tracks:
        if db_track.mbid not in enrichment:
            continue
        data = enrichment[db_track.mbid]
        suffix = _build_suffix(data['suffix_parts'])

        if suffix:
            new_title = f'{data["mb_title"]} {suffix}'
            if db_track.title != new_title:
                print(f'  ~ "{db_track.title}" → "{new_title}"')
                db_track.title = new_title
                titles_updated += 1

        existing_mbids = {a.mbid for a in db_track.artists}
        for a_data in data['extra_artists']:
            if a_data['mbid'] in existing_mbids:
                continue
            artist_obj, created = _get_or_create_artist(a_data['mbid'], a_data['name'])
            db_track.artists.append(artist_obj)
            artists_linked += 1
            if created:
                artists_created += 1
                print(f'  + Created artist: {a_data["name"]}')

    return titles_updated, artists_linked, artists_created, 0


def restore_feat_titles(debug_album=None):
    with app.app_context():
        albums = Album.query.order_by(Album.title).all()
        if debug_album:
            albums = [a for a in albums if debug_album.lower() in a.title.lower()]
            print(f'Debug mode — {len(albums)} album(s) matched "{debug_album}"\n')
        else:
            print(f'Processing {len(albums)} albums...\n')

        total_titles_updated = total_artists_linked = total_artists_created = total_skipped = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else ''
            print(f'[{i + 1}/{len(albums)}] {album.title} — {artist_name}')

            titles_updated, artists_linked, artists_created, skipped = _enrich_feat_titles_for_album(album)

            if skipped:
                print(f'  ✗ No MB data, skipping')
                total_skipped += 1
                continue

            db.session.commit()
            if titles_updated or artists_linked:
                print(f'  ✓ Titles: {titles_updated} | Artists linked: {artists_linked} (new: {artists_created})')
            else:
                print(f'  Already up to date')

            total_titles_updated += titles_updated
            total_artists_linked += artists_linked
            total_artists_created += artists_created

        print(f'\n── Summary ──────────────────────────────────────')
        print(f'Titles updated:   {total_titles_updated}')
        print(f'Artists linked:   {total_artists_linked}')
        print(f'Artists created:  {total_artists_created}')
        print(f'Albums skipped:   {total_skipped}')


# ── Color extraction ───────────────────────────────────────────────────────────

REQUEST_DELAY = 0.15


def _extract_dominant_color(url, timeout=10):
    try:
        resp = requests.get(url, timeout=timeout, headers=HEADERS)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert('RGB')
        img = img.resize((100, 100), Image.LANCZOS)

        paletted = img.quantize(colors=8)
        palette = paletted.getpalette()[:8 * 3]
        candidates = [(palette[i], palette[i+1], palette[i+2]) for i in range(0, 8*3, 3)]

        best, best_score = None, -1
        for r, g, b in candidates:
            _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if v < 0.12 or (v > 0.95 and s < 0.1):
                continue
            score = s * v
            if score > best_score:
                best_score, best = score, (r, g, b)

        if best is None:
            pixels = list(img.getdata())
            best = (
                sum(p[0] for p in pixels) // len(pixels),
                sum(p[1] for p in pixels) // len(pixels),
                sum(p[2] for p in pixels) // len(pixels),
            )

        return '#{:02x}{:02x}{:02x}'.format(*best)
    except Exception as e:
        print(f'    ✗ {e}')
        return None


def _avg_hex(hex_colors):
    rgbs = []
    for h in hex_colors:
        try:
            rgbs.append((int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)))
        except (ValueError, IndexError):
            continue
    if not rgbs:
        return None
    return '#{:02x}{:02x}{:02x}'.format(
        sum(x[0] for x in rgbs) // len(rgbs),
        sum(x[1] for x in rgbs) // len(rgbs),
        sum(x[2] for x in rgbs) // len(rgbs),
    )


def extract_colors(force=False):
    with app.app_context():
        if force:
            albums = Album.query.filter(Album.cover_url.isnot(None)).order_by(Album.id).all()
        else:
            albums = (
                Album.query
                .filter(Album.cover_url.isnot(None))
                .filter(Album.color_accent.is_(None))
                .order_by(Album.id)
                .all()
            )

        total = len(albums)
        print(f'Extracting colors for {total} albums...\n')
        done, failed = 0, 0

        for i, album in enumerate(albums):
            print(f'[{i + 1}/{total}] {album.title}')
            color = _extract_dominant_color(album.cover_url)
            if color:
                album.color_accent = color
                db.session.commit()
                print(f'  → {color}')
                done += 1
            else:
                failed += 1
            time.sleep(REQUEST_DELAY)

        print(f'\nAlbums done: {done} set, {failed} failed.')

        # Compute artist averages from album colors
        artists = Artist.query.filter(Artist.color_accent.is_(None)).all() if not force \
            else Artist.query.all()
        print(f'\nComputing accent colors for {len(artists)} artists...\n')
        a_done, a_skipped = 0, 0

        for artist in artists:
            color = _avg_hex([a.color_accent for a in artist.albums if a.color_accent])
            if color:
                artist.color_accent = color
                db.session.commit()
                print(f'  {artist.name:40s} → {color}')
                a_done += 1
            else:
                a_skipped += 1

        print(f'\nArtists done: {a_done} set, {a_skipped} skipped.')


# ── Manual album seed by release MBID ─────────────────────────────────────────

def seed_by_mbid(release_mbid):
    """
    Seed or update a specific album by its MusicBrainz release MBID.
    If the album already exists (matched by MBID or by title+artist),
    updates its MBID, year, cover, and tracklist in place.
    """
    with app.app_context():
        # Fetch the release
        release_data = search_mb_rels('release', release_mbid, inc='recordings+artist-credits')
        if not release_data:
            print(f'No data returned for MBID {release_mbid}')
            return

        normalized = normalize_release(release_data)
        if not normalized['mbid']:
            print('Could not parse release MBID from response')
            return

        title = normalized['title']
        artists_data = normalized['artists']

        # normalize_release checks first-release-date (release-group field);
        # direct release lookups use 'date' instead — check both
        raw_date = (
            release_data.get('date') or
            release_data.get('first-release-date') or
            release_data.get('release-group', {}).get('first-release-date', '')
        )
        try:
            year = int(raw_date[:4]) if raw_date and len(raw_date) >= 4 else normalized['release_date']
        except (ValueError, TypeError):
            year = normalized['release_date']

        print(f'Release: {title} ({year})')
        print(f'Artists: {", ".join(a["name"] for a in artists_data)}')

        # Try to find existing album — first by current MBID, then by title+primary artist
        album = Album.query.filter_by(mbid=release_mbid).first()
        if not album and artists_data:
            artist_obj = Artist.query.filter_by(mbid=artists_data[0]['mbid']).first()
            if artist_obj:
                album = Album.query.filter(
                    Album.title.ilike(title),
                    Album.artists.any(Artist.id == artist_obj.id)
                ).first()

        if album:
            print(f'Found existing album (ID {album.id}) — updating.')
            old_mbid = album.mbid
            if old_mbid != release_mbid:
                print(f'  MBID: {old_mbid} → {release_mbid}')
                album.mbid = release_mbid
            if album.title != title:
                print(f'  Title: "{album.title}" → "{title}"')
                album.title = title
            if year:
                if album.release_year != year:
                    print(f'  Year: {album.release_year} → {year}')
                album.release_year = year
        else:
            print('No existing album found — creating new entry.')
            album = Album(mbid=release_mbid, title=title, release_year=year)
            db.session.add(album)

        # Cover art
        cover_url, _ = get_cover_url(release_data.get('release-group', {}).get('id', ''))
        if cover_url:
            album.cover_url = cover_url
            print(f'  Cover: ✓')

        # Replace artist credits fully — resolves stale or incorrect primary artists
        new_artists = []
        for a_data in artists_data:
            if not a_data['mbid']:
                continue
            artist_obj = Artist.query.filter_by(mbid=a_data['mbid']).first()
            if not artist_obj:
                artist_obj = Artist(mbid=a_data['mbid'], name=a_data['name'])
                db.session.add(artist_obj)
                print(f'  New artist: {a_data["name"]}')
            elif artist_obj.name != a_data['name']:
                print(f'  Artist name: "{artist_obj.name}" → "{a_data["name"]}"')
                artist_obj.name = a_data['name']
            new_artists.append(artist_obj)

        if new_artists:
            album.artists = new_artists

        db.session.flush()

        # Rebuild tracklist
        media = release_data.get('media', [])
        existing_by_mbid = {t.mbid: t for t in album.tracks if t.mbid}
        existing_by_pos = {(t.disc_number, t.track_number): t for t in album.tracks}
        _feat_re = re.compile(r'\(feat\.?|ft\.?|featuring|with\b', re.IGNORECASE)

        added = updated = 0
        for disc in media:
            disc_number = disc.get('position', 1)
            for track in disc.get('tracks', []):
                recording = track.get('recording', {})
                mbid = recording.get('id')
                title_t = track.get('title') or recording.get('title')
                duration_ms = track.get('length')
                track_number = track.get('position')
                pos_key = (disc_number, track_number)

                if mbid and mbid in existing_by_mbid:
                    db_track = existing_by_mbid[mbid]
                    if db_track.title != title_t and title_t and not _feat_re.search(db_track.title):
                        print(f'  ~ "{db_track.title}" → "{title_t}"')
                        db_track.title = title_t
                        updated += 1
                elif pos_key in existing_by_pos:
                    db_track = existing_by_pos[pos_key]
                    if db_track.title != title_t and title_t and not _feat_re.search(db_track.title):
                        print(f'  ~ "{db_track.title}" → "{title_t}"')
                        db_track.title = title_t
                        if mbid:
                            db_track.mbid = mbid
                        updated += 1
                else:
                    if mbid and Track.query.filter_by(mbid=mbid).first():
                        continue
                    db.session.add(Track(
                        mbid=mbid,
                        title=title_t,
                        duration_ms=duration_ms,
                        track_number=track_number,
                        disc_number=disc_number,
                        album_id=album.id
                    ))
                    added += 1

        # Enrich feat. titles using the already-fetched release data
        t_updated, a_linked, a_created, _ = _enrich_feat_titles_for_album(album, release_data=release_data)

        try:
            db.session.commit()
            print(f'\nDone. Tracks added: {added} | Titles updated: {updated + t_updated} | Artists linked: {a_linked}')
        except Exception as e:
            db.session.rollback()
            print(f'Commit failed: {e}')


# ── Track refresh for recent albums ───────────────────────────────────────────

def refresh_recent_tracks(since_year=2025):
    """
    Re-fetch tracklists from MusicBrainz for all albums released in since_year
    or later. Adds missing tracks and updates TBD/placeholder titles.
    Never deletes existing tracks.
    """
    with app.app_context():
        albums = (
            Album.query
            .filter(Album.release_year >= since_year)
            .order_by(Album.release_year.desc(), Album.title)
            .all()
        )
        print(f'Refreshing tracks for {len(albums)} albums from {since_year}+\n')

        total_added = 0
        total_updated = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else ''
            print(f'[{i + 1}/{len(albums)}] {album.title} — {artist_name} ({album.release_year})')

            release_data = search_mb_rels('release', album.mbid, inc='recordings')
            if not release_data:
                print(f'  ✗ No MB data, skipping')
                continue

            media = release_data.get('media', [])
            if not media:
                print(f'  No media found, skipping')
                continue

            existing_by_mbid = {t.mbid: t for t in album.tracks if t.mbid}
            existing_by_pos = {(t.disc_number, t.track_number): t for t in album.tracks}
            _feat_re = re.compile(r'\(feat\.?|ft\.?|featuring|with\b', re.IGNORECASE)

            added = 0
            updated = 0

            for disc in media:
                disc_number = disc.get('position', 1)
                for track in disc.get('tracks', []):
                    recording = track.get('recording', {})
                    mbid = recording.get('id')
                    title = track.get('title') or recording.get('title')
                    duration_ms = track.get('length')
                    track_number = track.get('position')
                    pos_key = (disc_number, track_number)

                    if mbid and mbid in existing_by_mbid:
                        # Track exists — update title only if not already feat-enriched
                        db_track = existing_by_mbid[mbid]
                        if db_track.title != title and title and not _feat_re.search(db_track.title):
                            print(f'  ~ "{db_track.title}" → "{title}"')
                            db_track.title = title
                            updated += 1
                    elif pos_key in existing_by_pos:
                        # Same position, different or missing mbid — update title
                        db_track = existing_by_pos[pos_key]
                        if db_track.title != title and title and not _feat_re.search(db_track.title):
                            print(f'  ~ "{db_track.title}" → "{title}"')
                            db_track.title = title
                            if mbid:
                                db_track.mbid = mbid
                            updated += 1
                    else:
                        # New track — check globally to avoid unique constraint on mbid
                        if mbid and Track.query.filter_by(mbid=mbid).first():
                            continue
                        db.session.add(Track(
                            mbid=mbid,
                            title=title,
                            duration_ms=duration_ms,
                            track_number=track_number,
                            disc_number=disc_number,
                            album_id=album.id
                        ))
                        added += 1

            try:
                db.session.commit()
                if added or updated:
                    print(f'  ✓ Added: {added} | Updated: {updated}')
                else:
                    print(f'  Already up to date')
                total_added += added
                total_updated += updated
            except Exception as e:
                db.session.rollback()
                print(f'  ✗ Commit failed: {e}')

        print(f'\n── Summary ──────────────────────────────────────')
        print(f'Tracks added:   {total_added}')
        print(f'Titles updated: {total_updated}')


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else 'missing-albums'

    mbid_flag = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--mbid=')), None)

    if mode == 'seed' and mbid_flag:
        seed_by_mbid(mbid_flag)
    elif mode == 'reseed-albums':
        reseed_existing_albums()
    elif mode == 'force-albums':
        seed_artist_albums(mode='force')
    elif mode == 'missing-albums':
        seed_artist_albums(mode='missing')
    elif mode == 'new-artists':
        seed_new_artists()
    elif mode == 'covers':
        update_cover_art()
    elif mode == 'covers-force':
        update_cover_art(force=True)
    elif mode == 'feat-titles':
        debug = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--debug=')), None)
        restore_feat_titles(debug_album=debug)
    elif mode == 'colors':
        extract_colors()
    elif mode == 'colors-force':
        extract_colors(force=True)
    elif mode == 'refresh':
        year = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 2025
        refresh_recent_tracks(since_year=year)
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python seeds/seed.py [reseed-albums|force-albums|missing-albums|new-artists|covers|covers-force|feat-titles|colors|colors-force|refresh [year]]")
        print("       python seeds/seed.py seed --mbid=<release-mbid>")