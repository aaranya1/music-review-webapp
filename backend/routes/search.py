from flask import Blueprint, request, jsonify
from models import Album, Artist
from sqlalchemy.orm import selectinload

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'message': 'Missing query parameter'}), 400
    if len(query) > 100:
        return jsonify({'message': 'Query must be at most 100 characters'}), 400

    # Escape LIKE wildcards so a search for "_" or "%" is literal
    pattern = '%' + query.replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%'

    albums = (
        Album.query
        .options(selectinload(Album.artists))
        .filter(Album.title.ilike(pattern, escape='!'))
        .order_by(Album.title)
        .limit(20)
        .all()
    )

    artists = (
        Artist.query
        .filter(Artist.name.ilike(pattern, escape='!'))
        .order_by(Artist.name)
        .limit(10)
        .all()
    )

    return jsonify({
        'query': query,
        'albums': [{
            'mbid': a.mbid,
            'title': a.title,
            'release_year': a.release_date.year if a.release_date else None,
            'cover_url': a.cover_url,
            'artists': [{'mbid': ar.mbid, 'name': ar.name} for ar in a.artists]
        } for a in albums],
        'artists': [{
            'mbid': a.mbid,
            'name': a.name,
            'image_url': a.image_url
        } for a in artists]
    })