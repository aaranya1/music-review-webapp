from flask import Blueprint
from models import User, Review
from sqlalchemy import func
from flask import request
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

@users_bp.route('/users/<int:user_id>')
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    review_count = Review.query.filter_by(user_id=user.id).count()
    return {"id": user.id, "username": user.username, "review_count": review_count}

@users_bp.route('/users/<username>')
def get_profile(username):
    user = User.query.filter(func.lower(User.username) == username.lower()).first_or_404()
    review_count = Review.query.filter_by(user_id=user.id).count()
    return {"id": user.id, "username": user.username, "review_count": review_count}

@users_bp.route('/users/<int:user_id>/reviews')
def get_user_reviews(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = Review.query.options(*review_load_options()) \
        .filter_by(user_id=user.id) \
        .order_by(Review.created_at.desc(), Review.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return {"reviews": [serialize_review(r) for r in pagination.items],
            "page": pagination.page,
            "total_pages": pagination.pages,
            "total": pagination.total}
