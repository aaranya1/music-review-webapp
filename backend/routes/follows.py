from flask import Blueprint, g
from models import User, Follow
from db import db
from routes.auth import token_required
from notifications_service import create_notification

follows_bp = Blueprint('follows', __name__)


@follows_bp.route('/users/<int:user_id>/follow', methods=['POST'])
@token_required
def follow_user(user_id):
    if user_id == g.user_id:
        return {"message": "You cannot follow yourself"}, 400
    User.query.get_or_404(user_id)
    existing = Follow.query.filter_by(follower_id=g.user_id, following_id=user_id).first()
    if existing:
        return {"message": "Already following"}, 409
    follow = Follow(follower_id=g.user_id, following_id=user_id)
    db.session.add(follow)
    create_notification(
        user_id=user_id,
        actor_id=g.user_id,
        type_='new_follower',
        target_type='user',
        target_id=g.user_id,
    )
    db.session.commit()
    return {"message": "Followed"}, 201


@follows_bp.route('/users/<int:user_id>/follow', methods=['DELETE'])
@token_required
def unfollow_user(user_id):
    follow = Follow.query.filter_by(follower_id=g.user_id, following_id=user_id).first_or_404()
    db.session.delete(follow)
    db.session.commit()
    return {"message": "Unfollowed"}, 200


@follows_bp.route('/users/<int:user_id>/follow/status', methods=['GET'])
@token_required
def follow_status(user_id):
    exists = Follow.query.filter_by(follower_id=g.user_id, following_id=user_id).first()
    return {"following": exists is not None}


@follows_bp.route('/users/<int:user_id>/followers', methods=['GET'])
def get_followers(user_id):
    from flask import request
    User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    pagination = (
        Follow.query
        .filter_by(following_id=user_id)
        .order_by(Follow.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return {
        "followers": [
            {"id": f.follower.id, "username": f.follower.username}
            for f in pagination.items
        ],
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
    }


@follows_bp.route('/users/<int:user_id>/following', methods=['GET'])
def get_following(user_id):
    from flask import request
    User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    pagination = (
        Follow.query
        .filter_by(follower_id=user_id)
        .order_by(Follow.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return {
        "following": [
            {"id": f.following.id, "username": f.following.username}
            for f in pagination.items
        ],
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
    }
