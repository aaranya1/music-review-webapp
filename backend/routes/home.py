from flask import Blueprint, request, g
from models import Review, Follow, ReviewLike
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from routes.auth import token_required
from serializers import serialize_review

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def home():
    latest_reviews = (
        Review.query
        .options(selectinload(Review.album), selectinload(Review.likes))
        .order_by(Review.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "latest_reviews": [serialize_review(r) for r in latest_reviews]
    }


@home_bp.route('/feed')
@token_required
def feed():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    following_ids = (
        Follow.query
        .filter_by(follower_id=g.user_id)
        .with_entities(Follow.following_id)
        .subquery()
    )

    pagination = (
        Review.query
        .filter(Review.user_id.in_(following_ids))
        .options(selectinload(Review.album), selectinload(Review.likes))
        .order_by(Review.created_at.desc(), Review.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return {
        "reviews": [serialize_review(r) for r in pagination.items],
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
    }


@home_bp.route('/feed/popular')
def feed_popular():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    like_count = (
        func.count(ReviewLike.id).label('like_count')
    )

    pagination = (
        Review.query
        .outerjoin(ReviewLike, ReviewLike.review_id == Review.id)
        .group_by(Review.id)
        .options(selectinload(Review.album), selectinload(Review.likes))
        .order_by(like_count.desc(), Review.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return {
        "reviews": [serialize_review(r) for r in pagination.items],
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
    }