from flask import Blueprint, request, g
from models import Album, Backlog
from db import db
from routes.auth import token_required
from sqlalchemy.orm import selectinload

backlog_bp = Blueprint('backlog', __name__)


@backlog_bp.route('/backlog', methods=['GET'])
@token_required
def get_backlog():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = (
        Backlog.query
        .filter_by(user_id=g.user_id)
        .options(selectinload(Backlog.album))
        .order_by(Backlog.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return {
        "backlog": [
            {
                "id": entry.id,
                "added_at": entry.created_at,
                "album": {
                    "id": entry.album.id,
                    "mbid": entry.album.mbid,
                    "title": entry.album.title,
                    "cover_url": entry.album.cover_url,
                    "release_year": entry.album.release_date.year if entry.album.release_date else None,
                    "artists": [{"name": a.name, "mbid": a.mbid} for a in entry.album.artists],
                }
            }
            for entry in pagination.items
        ],
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
    }


@backlog_bp.route('/backlog/<string:album_mbid>', methods=['POST'])
@token_required
def add_to_backlog(album_mbid):
    album = Album.query.filter_by(mbid=album_mbid).first_or_404()
    existing = Backlog.query.filter_by(user_id=g.user_id, album_id=album.id).first()
    if existing:
        return {"message": "Already in backlog"}, 409
    entry = Backlog(user_id=g.user_id, album_id=album.id)
    db.session.add(entry)
    db.session.commit()
    return {"message": "Added to backlog"}, 201


@backlog_bp.route('/backlog/<string:album_mbid>', methods=['DELETE'])
@token_required
def remove_from_backlog(album_mbid):
    album = Album.query.filter_by(mbid=album_mbid).first_or_404()
    entry = Backlog.query.filter_by(user_id=g.user_id, album_id=album.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return {"message": "Removed from backlog"}, 200


@backlog_bp.route('/backlog/<string:album_mbid>/status', methods=['GET'])
@token_required
def backlog_status(album_mbid):
    album = Album.query.filter_by(mbid=album_mbid).first_or_404()
    exists = Backlog.query.filter_by(user_id=g.user_id, album_id=album.id).first()
    return {"in_backlog": exists is not None}
