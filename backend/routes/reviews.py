from flask import Blueprint, request, g
from models import Review, ReviewLike, ReviewComment, CommentLike
from db import db
from routes.auth import token_required
from sqlalchemy.orm import selectinload
from serializers import serialize_review
from notifications_service import create_notification

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/reviews')
def get_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = (
        Review.query
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

@reviews_bp.route('/reviews/<int:review_id>', methods=['PUT'])
@token_required
def update_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != g.user_id:
        return {"message": "Unauthorized"}, 403

    data = request.get_json()
    new_rating = data.get('rating', review.rating)

    if new_rating < 0 or new_rating > 5 or new_rating % 0.5 != 0:
        return {"message": "Rating must be between 0 and 5 in 0.5 increments"}, 400
    
    review.rating = new_rating
    review.review_text = data.get('review_text', review.review_text)
    review.updated_at = db.func.current_timestamp()

    db.session.commit()
    return {"message": "Review updated successfully"}, 200

@reviews_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@token_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != g.user_id:
        return {"message": "Unauthorized"}, 403

    db.session.delete(review)
    db.session.commit()
    return {"message": "Review deleted successfully"}, 200


# ── Review likes ──────────────────────────────────────────────────────────────

@reviews_bp.route('/reviews/<int:review_id>/like', methods=['POST'])
@token_required
def toggle_review_like(review_id):
    review = Review.query.get_or_404(review_id)
    existing = ReviewLike.query.filter_by(user_id=g.user_id, review_id=review_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {"liked": False}
    like = ReviewLike(user_id=g.user_id, review_id=review_id)
    db.session.add(like)
    create_notification(
        user_id=review.user_id,
        actor_id=g.user_id,
        type_='review_like',
        target_type='review',
        target_id=review.id,
    )
    db.session.commit()
    return {"liked": True}, 201


# ── Review comments ───────────────────────────────────────────────────────────

@reviews_bp.route('/reviews/<int:review_id>/comments', methods=['GET'])
@token_required
def get_review_comments(review_id):
    Review.query.get_or_404(review_id)
    comments = (
        ReviewComment.query
        .filter_by(review_id=review_id)
        .options(selectinload(ReviewComment.likes))
        .order_by(ReviewComment.created_at.asc())
        .all()
    )
    return {"comments": [
        {
            "id": c.id,
            "user_id": c.user_id,
            "username": c.user.username,
            "body": c.body,
            "media_url": c.media_url,
            "like_count": len(c.likes),
            "created_at": c.created_at,
        }
        for c in comments
    ]}


@reviews_bp.route('/reviews/<int:review_id>/comments', methods=['POST'])
@token_required
def create_review_comment(review_id):
    review = Review.query.get_or_404(review_id)
    data = request.get_json()
    body = data.get('body', '').strip()
    if not body:
        return {"message": "Comment body is required"}, 400
    comment = ReviewComment(
        user_id=g.user_id,
        review_id=review_id,
        body=body,
        media_url=data.get('media_url')
    )
    db.session.add(comment)
    db.session.flush()
    create_notification(
        user_id=review.user_id,
        actor_id=g.user_id,
        type_='new_comment',
        target_type='comment',
        target_id=comment.id,
    )
    db.session.commit()
    return {"message": "Comment created", "id": comment.id}, 201


@reviews_bp.route('/reviews/<int:review_id>/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_review_comment(review_id, comment_id):
    comment = ReviewComment.query.filter_by(id=comment_id, review_id=review_id).first_or_404()
    if comment.user_id != g.user_id:
        return {"message": "Unauthorized"}, 403
    db.session.delete(comment)
    db.session.commit()
    return {"message": "Comment deleted"}, 200


# ── Comment likes ─────────────────────────────────────────────────────────────

@reviews_bp.route('/reviews/<int:review_id>/comments/<int:comment_id>/like', methods=['POST'])
@token_required
def toggle_comment_like(review_id, comment_id):
    comment = ReviewComment.query.filter_by(id=comment_id, review_id=review_id).first_or_404()
    existing = CommentLike.query.filter_by(user_id=g.user_id, comment_id=comment_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {"liked": False}
    like = CommentLike(user_id=g.user_id, comment_id=comment_id)
    db.session.add(like)
    create_notification(
        user_id=comment.user_id,
        actor_id=g.user_id,
        type_='comment_like',
        target_type='comment',
        target_id=comment.id,
    )
    db.session.commit()
    return {"liked": True}, 201