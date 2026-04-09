from flask import Blueprint
from models import Album, Review, Track, Credit, ReviewLike, ReviewComment
from db import db
from routes.auth import token_required
from flask import request, g
from sqlalchemy.orm import selectinload

albums_bp = Blueprint('albums', __name__)

@albums_bp.route('/albums')
def get_albums():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = Album.query.options(selectinload(Album.artists)) \
        .order_by(Album.release_date.desc(), Album.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)
     
    output = []
    for album in pagination.items:
        album_data = {
            'mbid': album.mbid, 
            'title': album.title, 
            'release_year': album.release_date.year if album.release_date else None,
            'cover_url': album.cover_url,
            'artists': [{'mbid': artist.mbid, 'name': artist.name} 
                        for artist in album.artists],
            #'average rating': (
            #    round(sum(r.rating for r in album.reviews) / len(album.reviews), 2) if album.reviews else None
            #)
        }
        output.append(album_data)    
    
    return {"albums": output,
            "page": pagination.page,
            "total_pages": pagination.pages,
            "total": pagination.total
            }

@albums_bp.route('/albums/<string:mbid>')
def get_album(mbid):
    album = Album.query \
        .options(
            selectinload(Album.artists),
            selectinload(Album.tracks).selectinload(Track.credits),
            selectinload(Album.tracks).selectinload(Track.artists),
            selectinload(Album.reviews)
        ) \
        .filter_by(mbid=mbid) \
        .first_or_404()
    
    discs = {}
    for track in album.tracks:
        disc = track.disc_number or 1
        if disc not in discs:
            discs[disc] = []
        discs[disc].append({
            'track_number': track.track_number,
            'title': track.title,
            'duration_ms': track.duration_ms,
            'artists': [
                {'mbid': a.mbid, 'name': a.name}
                for a in track.artists
            ],
            'credits': [
                {
                    'artist_name': credit.artist_name,
                    'role': credit.role
                }
                for credit in track.credits
            ]
        })
    
    for disc in discs:
        discs[disc].sort(key=lambda t: t['track_number'])

    tracklist = [
        {'disc_number': disc, 'tracks': discs[disc]}
        for disc in sorted(discs.keys())
    ]

    average_rating = (
        round(sum(r.rating for r in album.reviews) / len(album.reviews), 2)
        if album.reviews else None
    )

    return {
        "mbid": album.mbid,
        "title": album.title,
        "release_year": album.release_date.year if album.release_date else None,
        "release_date": album.release_date.isoformat() if album.release_date else None,
        "cover_url": album.cover_url,
        "artists": [{'mbid': artist.mbid, 'name': artist.name} for artist in album.artists],
        "tracklist": tracklist,
        "review_count": len(album.reviews),
        "average_rating": average_rating,
        "color_accent": album.color_accent,
    }

@albums_bp.route('/albums/<string:mbid>/reviews')
def get_album_reviews(mbid):
    album = Album.query.filter_by(mbid=mbid).first_or_404()
    reviews = (
        Review.query
        .filter_by(album_id=album.id)
        .options(
            db.joinedload(Review.user),
            selectinload(Review.likes),
            selectinload(Review.comments),
        )
        .all()
    )
    album_reviews = []
    for review in reviews:
        album_reviews.append({
            "id": review.id,
            "user_id": review.user_id,
            "username": review.user.username,
            "rating": review.rating,
            "comment": review.review_text,
            "like_count": len(review.likes),
            "comment_count": len(review.comments),
            "created_at": review.created_at,
            "updated_at": review.updated_at
        })
    return {"reviews": album_reviews}

@albums_bp.route('/albums/<string:mbid>/reviews', methods=['POST'])
@token_required
def create_review(mbid):
    album = Album.query.filter_by(mbid=mbid).first_or_404()
    data = request.get_json()
    input_rating = data.get('rating')

    existing = Review.query.filter_by(
        user_id=g.user_id,
        album_id=album.id
    ).first()

    if existing:
        return {"message": "Review already exists"}, 409

    if input_rating < 0 or input_rating > 5 or input_rating % 0.5 != 0:
        return {"message": "Rating must be between 0 and 5 in 0.5 increments"}, 400
    
    new_review = Review(
        user_id=g.user_id,
        album_id=album.id,
        rating=input_rating,
        review_text=data.get('review_text', '')
    )
    db.session.add(new_review)
    db.session.commit()
    return {"message": "Review created successfully"}, 201