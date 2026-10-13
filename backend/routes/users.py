from flask import Blueprint, g
from models import User, Review, Follow
from sqlalchemy import func
from flask import request
from routes.auth import optional_auth
from serializers import serialize_review, review_load_options

users_bp = Blueprint('users', __name__)

'''
@users_bp.route('/users')
def get_users():
    users = User.query.all()
    output = []
    for user in users:
        output.append({'id': user.id, 'username': user.username, 'email': user.email})

    return {"users": output}
'''


def _serialize_profile(user):
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
        "review_count": Review.query.filter_by(user_id=user.id).count(),
        "follower_count": Follow.query.filter_by(following_id=user.id).count(),
        "following_count": Follow.query.filter_by(follower_id=user.id).count(),
        # None when logged out, so the client can tell "not following" from "unknown"
        "is_following": (
            None if g.user_id is None
            else Follow.query.filter_by(follower_id=g.user_id, following_id=user.id).first() is not None
        ),
    }

@users_bp.route('/users/<int:user_id>')
@optional_auth
def get_user(user_id):
    return _serialize_profile(User.query.get_or_404(user_id))

@users_bp.route('/users/<username>')
@optional_auth
def get_profile(username):
    user = User.query.filter(func.lower(User.username) == username.lower()).first_or_404()
    return _serialize_profile(user)

@users_bp.route('/users/<int:user_id>/reviews')
@optional_auth
def get_user_reviews(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = Review.query.options(*review_load_options()) \
        .filter_by(user_id=user.id) \
        .order_by(Review.created_at.desc(), Review.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return {"reviews": [serialize_review(r, g.user_id) for r in pagination.items],
            "page": pagination.page,
            "total_pages": pagination.pages,
            "total": pagination.total}
