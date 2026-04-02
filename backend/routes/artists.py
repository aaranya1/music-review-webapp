from flask import Blueprint
from models import Artist
from flask import request
from sqlalchemy.orm import selectinload

artists_bp = Blueprint('artists', __name__)

@artists_bp.route('/artists')
def get_artists():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = Artist.query.order_by(Artist.id).paginate(page=page, per_page=per_page, error_out=False)     
    output = []
    for artist in pagination.items:
        artist_data = {
            'mbid': artist.mbid,
            'name': artist.name,
            'image_url': artist.image_url,
            'background_url': artist.background_url,
        }
        output.append(artist_data)    
    
    return {"artists": output,
            "page": pagination.page,
            "total_pages": pagination.pages,
            "total": pagination.total
            }

@artists_bp.route('/artists/<string:mbid>')
def get_artist(mbid):
    artist = Artist.query.options(selectinload(Artist.albums)) \
        .filter_by(mbid=mbid).first_or_404()
    
    return {
        "id": artist.id, 
        "mbid": artist.mbid,
        "name": artist.name, 
        "albums": [
            {'mbid': album.mbid, 
             'title': album.title, 
             'release_year': album.release_year,
             'cover_url': album.cover_url } for album in artist.albums],
        "image_url": artist.image_url,
        "background_url": artist.background_url,
        "country": artist.country,
        "color_accent": artist.color_accent,
    }
