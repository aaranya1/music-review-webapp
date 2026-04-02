import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app
from db import db
from models import Album, Artist, Track
from services.musicbrainz import search_mb, search_cover_art, normalize_release, search_mb_rels
import requests
import time
import re
import colorsys
from io import BytesIO
from PIL import Image

HEADERS = {
    'User-Agent': os.getenv('MB_USER_AGENT', 'MusicApp/1.0')
}

SECONDARY_TYPE_BLOCKLIST = {
    "live", "compilation", "dj-mix", "spokenword",
    "remix", "interview", "soundtrack"
}

# ── Artists to seed ────────────────────────────────────────────────────────────
# Add artists here to grow the database. Already-seeded artists can be included
# safely — the script skips albums already in the DB.

NEW_ARTISTS = [
    # Rock / Alt
    "Radiohead",
    "Tame Impala",
    "The Strokes",
    "Arctic Monkeys",  # reseed — EPs now included
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
    "Kendrick Lamar",   # reseed — EPs now included
    "J. Cole",          # reseed
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
    #Dondon
    "Good Kid",
    "TWRP",
    "My Chemical Romance",
    "Pierce the veil",
    "Waterparks",
    "Laufey",
    "Mitski",
    "Panchiko",
    "Gloc-9",
    "Eraserheads",
    "Asin",
    "MF DOOM",
    "Queen",
    "Green Day",
    "Panic! At The Disco",
    "I DONT KNOW HOW BUT THEY FOUND ME",
    "BINI", 
    "RED VELVET",
    "Le SSerafim",
    "The living tombstone",
    "Odyssey Eurobeat",
    "Dave Rogers",
    "Fleetwood Mac",
    "OutKast",
    "Skindread",
    "System Of a Down",
    "Iron Maiden",
    "Metallica",
    "Megadeath",
    "Black Sabbath",
    "Judas Priest",
    "Paramore",
    "Hozier",
    "Kate Bush", 
    "Bowling for soup",
    "Elliot Smith",
    "The Cure",
    "beabadobee",

    #Toast
    "Hail the Sun",
    "Machine Girl",
    "2Hollis",
    "Omerta",
    "Mella",
    "Nick Drake",

    #Lily
    "Linkin Park",
    "Imagine Dragons",
    "Avicii",
    "Twenty One Pilots",
    "Unlike Pluto",
    "Falling in Reverse",
    "Written by Wolves",
    "Emlyn",
    "Kendrick Lamar",
    "STARSET",
    "Lady Gaga",
    "JVKE",
    "Fall Out Boy",
    "Tyler, The Creator",
    "My Chemical Romance",
    "Sam Tinnesz",
    "Porter Robinson",
    "bbno$",
    "Alex Warren",
    "Rain Paris",
    "Peyton Parrish",
    "Jonathan Young",
    "Citizen Soldier",
    "TROY",
    "Derivakat",
    "Hozier",
    "Jorge Rivera-Herrans",
    "Cristina Vee",
    "Apashe",
    "Paramore",
    "Red Hot Chili Peppers",
    "Arctic Monkeys",
    "Idris Elba",
    "KE$HA",
    "Rihanna",
    "Morgan St. Jean",
    "Xana",
    "Halsey",
    "Doja Cat",
    "Cloudy June",
    "EMELINE",
    "Doechii",
    "Slipknot",
    "Rage Against the Machine",
    "Three Days Grace",
    "HUNTR/X",
    "Mumford & Sons",
    "The Living Tombstone",
    "Celtic Woman",
    "Pierce the Veil",
    "Florence  the Machine",
    "SAMURAI",
    "CG5",
    "The Hush Sound",
    "SKÁLD",
    "Olivia Rodrigo",
    "Jon Bellion",

    #Megan
    "My chemical romance",
    "Hozier",
    "Linkin park",
    "Sabrina carpenter",
    "Pierce the veil",
    "Ado",
    "Fuji kaze",
    "Green Day",
    "Mindless self indulgence",
    "Lady Gaga",
    "Crown the empire",
    "Måneskin",
    "Muse",

    #Harlow
    "One Direction", 
    "The Smiths",
    "Yarlokre", 
    "Fleetwood Mac", 
    "ABBA", 
    "Amélie Farren", 
    "Glass Animals", 
    "Chromatics", 
    "Dean Martin",
]

MISC_ARTISTS = [
    "Skindred",
    "Elliott Smith",
    "beabadoobee",
    "Yaelokre",
    "The 1975",
    "Tom Odell",
    "Kodaline",
    "Oklou",
    "Joji",
    "Dijon",
    "Geese",
    "Sam Gellaitry",
    "Before You Exit",
    "Poets of the Fall",
    "Gesaffelstein",
    "St. Vincent",
    "Yebba",
    "Majid Jordan",
    "Mark Ronson",
    "Amy Winehouse",
    "U2",
    "KAYTRANADA",
    "Yves",
    "Malcolm Todd",
    "Justice",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def verify_cover_url(url, timeout=6):
    """HEAD request to check the cover URL actually resolves."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def get_cover_url(rg_mbid):
    """
    Fetch cover art for a release group.
    Returns (cover_url_500, release_id) or (None, None).
    Uses 500px thumbnail for quality; falls back to raw image URL.
    """
    cover_json = search_cover_art(rg_mbid)
    images = cover_json.get('images', [])
    if not images:
        return None, None

    first_image = images[0]
    image_url = first_image.get('image', '')

    # Extract release MBID from the image URL
    reid = None
    parts = image_url.split('/')
    if 'release' in parts:
        idx = parts.index('release')
        reid = parts[idx + 1] if idx + 1 < len(parts) else None

    # Prefer 500px thumbnail, fall back to 250px, then raw
    thumbnails = first_image.get('thumbnails', {})
    cover_url = (
        thumbnails.get('500') or
        thumbnails.get('large') or
        thumbnails.get('250') or
        image_url
    )

    if cover_url and not verify_cover_url(cover_url):
        print(f"  Cover URL did not resolve, skipping.")
        return None, reid

    return cover_url, reid


def seed_tracks_for_album(album):
    """Fetch and seed tracks for a single album."""
    release_data = search_mb_rels('release', album.mbid, inc='recordings')
    if not release_data:
        return 0

    media = release_data.get('media', [])
    if not media:
        return 0

    count = 0
    for disc in media:
        disc_number = disc.get('position', 1)
        for track in disc.get('tracks', []):
            recording = track.get('recording', {})
            mbid = recording.get('id')
            if mbid and Track.query.filter_by(mbid=mbid).first():
                continue
            t = Track(
                mbid=mbid,
                title=track.get('title') or recording.get('title'),
                duration_ms=track.get('length'),
                track_number=track.get('position'),
                disc_number=disc_number,
                album_id=album.id
            )
            db.session.add(t)
            count += 1

    return count


# ── Main seed ──────────────────────────────────────────────────────────────────

def seed(artists_to_seed=None, include_eps=True, max_albums=10, max_eps=4, seed_tracks=True):
    """
    Args:
        artists_to_seed: list of artist name strings. Defaults to NEW_ARTISTS.
        include_eps:     whether to also seed EPs.
        max_albums:      max studio albums to seed per artist.
        max_eps:         max EPs to seed per artist (only used if include_eps=True).
        seed_tracks:     whether to seed tracks after seeding albums.
    """
    if artists_to_seed is None:
        artists_to_seed = MISC_ARTISTS

    with app.app_context():
        artist_cache = {}

        for artist_name in artists_to_seed:
            print(f"\n── {artist_name} ──")

            if Artist.query.filter(Artist.name.ilike(artist_name)).first():
                print(f" Already in DB, skipping.")
                continue

            # Phase 1: Find artist MBID
            artist_data = search_mb('artist', artist_name, 1)
            artists = artist_data.get('artists', [])
            if not artists:
                print(f"  Could not find MBID, skipping.")
                continue
            artist_mbid = artists[0]['id']

            # Phase 2: Fetch release groups — albums and optionally EPs
            rg_base = f'arid:{artist_mbid} AND status:official'

            album_rgs = search_mb(
                'release-group',
                f'{rg_base} AND primarytype:album',
                limit=30
            ).get('release-groups', [])

            ep_rgs = []
            if include_eps:
                ep_rgs = search_mb(
                    'release-group',
                    f'{rg_base} AND primarytype:ep',
                    limit=15
                ).get('release-groups', [])

            # Phase 3: Filter secondary types and sort newest first
            def filter_and_sort(rgs):
                valid = []
                for rg in rgs:
                    secondary = [t.lower() for t in rg.get('secondary-types', [])]
                    if any(t in SECONDARY_TYPE_BLOCKLIST for t in secondary):
                        continue
                    valid.append(rg)
                return sorted(valid, key=lambda x: x.get('first-release-date', ''), reverse=True)

            valid_albums = filter_and_sort(album_rgs)[:max_albums]
            valid_eps = filter_and_sort(ep_rgs)[:max_eps]
            all_rgs = valid_albums + valid_eps

            print(f"  Found {len(valid_albums)} albums, {len(valid_eps)} EPs to process.")

            # Phase 4 & 5: Fetch cover + release, normalize, seed
            for rg in all_rgs:
                rg_mbid = rg.get('id')
                rg_date = rg.get('first-release-date', '')
                rg_type = 'EP' if rg in valid_eps else 'Album'

                cover_url, reid = get_cover_url(rg_mbid)

                if reid:
                    release_params = f'reid:{reid}'
                else:
                    release_params = f'rgid:{rg_mbid} AND status:official'

                releases = search_mb('release', release_params, 1).get('releases', [])
                if not releases:
                    print(f"  No release found for {rg.get('title')}, skipping.")
                    continue

                release_dict = releases[0]
                release_dict['release-group'] = {
                    **release_dict.get('release-group', {}),
                    'first-release-date': rg_date,
                }
                release_dict['cover_url'] = cover_url

                normalized = normalize_release(release_dict)

                if not normalized['release_date']:
                    print(f"  Skipping {normalized['title']} (no valid year)")
                    continue

                if not normalized['mbid']:
                    print(f"  Skipping {normalized['title']} (no MBID)")
                    continue

                # Skip if already in DB
                album = Album.query.filter_by(mbid=normalized['mbid']).first()
                if album:
                    print(f"  Already exists: {album.title} — checking tracks.")
                    if seed_tracks and not album.tracks:
                        track_count = seed_tracks_for_album(album)
                        db.session.commit()
                        print(f"  Added {track_count} tracks.")
                    continue

                # Create album
                album = Album(
                    mbid=normalized['mbid'],
                    title=normalized['title'],
                    release_year=normalized['release_date'],
                    cover_url=cover_url
                )
                db.session.add(album)

                # Attach artists
                for artist_info in normalized['artists']:
                    if not artist_info['mbid']:
                        continue

                    artist_obj = artist_cache.get(artist_info['mbid'])
                    if not artist_obj:
                        artist_obj = Artist.query.filter_by(mbid=artist_info['mbid']).first()
                    if not artist_obj:
                        artist_obj = Artist(
                            mbid=artist_info['mbid'],
                            name=artist_info['name']
                        )
                        db.session.add(artist_obj)
                        print(f"  New artist: {artist_obj.name}")

                    artist_cache[artist_info['mbid']] = artist_obj
                    album.artists.append(artist_obj)

                db.session.flush()  # get album.id before seeding tracks

                # Seed tracks immediately
                track_count = 0
                if seed_tracks:
                    track_count = seed_tracks_for_album(album)

                db.session.commit()
                print(f"  [{rg_type}] {album.title} ({album.release_year}) — {track_count} tracks | cover: {'✓' if cover_url else '✗'}")

        print("\nSeeding complete.")


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


def restore_feat_titles(debug_album=None):
    with app.app_context():
        albums = Album.query.order_by(Album.title).all()
        if debug_album:
            albums = [a for a in albums if debug_album.lower() in a.title.lower()]
            print(f'Debug mode — {len(albums)} album(s) matched "{debug_album}"\n')
        else:
            print(f'Processing {len(albums)} albums...\n')

        total_titles_updated = 0
        total_artists_linked = 0
        total_artists_created = 0
        total_skipped = 0

        for i, album in enumerate(albums):
            artist_name = album.artists[0].name if album.artists else ''
            album_artist_mbids = {a.mbid for a in album.artists}
            print(f'[{i + 1}/{len(albums)}] {album.title} — {artist_name}')

            release_data = search_mb_rels('release', album.mbid, inc='recordings+artist-credits')
            if not release_data:
                print(f'  ✗ No MB data, skipping')
                total_skipped += 1
                continue

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
                    if debug_album:
                        credit_str = ''.join(
                            c.get('artist', {}).get('name', '') + c.get('joinphrase', '')
                            for c in credits
                        ).strip()
                        print(f'  MB: "{mb_title}" | credits: "{credit_str}"')
                        print(f'      suffix → {_build_suffix(suffix_parts)} | extra → {[a["name"] for a in extra_artists]}')
                    enrichment[recording_mbid] = {
                        'mb_title': mb_title,
                        'suffix_parts': suffix_parts,
                        'extra_artists': extra_artists,
                    }

            if not enrichment:
                print(f'  No multi-artist tracks found')
                continue

            titles_updated = 0
            artists_linked = 0
            artists_created = 0

            for db_track in album.tracks:
                if db_track.mbid not in enrichment:
                    continue
                data = enrichment[db_track.mbid]
                suffix = _build_suffix(data['suffix_parts'])
                extra_artists = data['extra_artists']
                mb_title = data['mb_title']

                if suffix:
                    new_title = f'{mb_title} {suffix}'
                    if db_track.title != new_title:
                        print(f'  ~ "{db_track.title}" → "{new_title}"')
                        db_track.title = new_title
                        titles_updated += 1

                existing_mbids = {a.mbid for a in db_track.artists}
                for a_data in extra_artists:
                    if a_data['mbid'] in existing_mbids:
                        continue
                    artist_obj, created = _get_or_create_artist(a_data['mbid'], a_data['name'])
                    db_track.artists.append(artist_obj)
                    artists_linked += 1
                    if created:
                        artists_created += 1
                        print(f'  + Created artist: {a_data["name"]}')

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


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else 'seed'

    if mode == 'seed':
        seed()
    elif mode == 'covers':
        update_cover_art()
    elif mode == 'covers-force':
        update_cover_art(force=True)
    elif mode == 'tracks':
        with app.app_context():
            albums = Album.query.filter(~Album.tracks.any()).all()
            print(f"Found {len(albums)} albums missing tracks.")
            for album in albums:
                print(f"  {album.title}")
                count = seed_tracks_for_album(album)
                db.session.commit()
                print(f"  Added {count} tracks.")
            print("Done.")
    elif mode == 'feat-titles':
        debug = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--debug=')), None)
        restore_feat_titles(debug_album=debug)
    elif mode == 'colors':
        extract_colors()
    elif mode == 'colors-force':
        extract_colors(force=True)
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python seeds/seed.py [seed|tracks|covers|covers-force|feat-titles|colors|colors-force]")