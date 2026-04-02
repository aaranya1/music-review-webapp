from flask import Blueprint, request, jsonify
from models import Album, Artist
from sqlalchemy.orm import selectinload

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400

    albums = (
        Album.query
        .options(selectinload(Album.artists))
        .filter(Album.title.ilike(f'%{query}%'))
        .order_by(Album.title)
        .limit(20)
        .all()
    )

    artists = (
        Artist.query
        .filter(Artist.name.ilike(f'%{query}%'))
        .order_by(Artist.name)
        .limit(10)
        .all()
    )

    return jsonify({
        'query': query,
        'albums': [{
            'mbid': a.mbid,
            'title': a.title,
            'release_year': a.release_year,
            'cover_url': a.cover_url,
            'artists': [{'mbid': ar.mbid, 'name': ar.name} for ar in a.artists]
        } for a in albums],
        'artists': [{
            'mbid': a.mbid,
            'name': a.name,
            'image_url': a.image_url
        } for a in artists]
    })