from flask import Blueprint
from models import Review
from db import db
from routes.auth import token_required
from flask import request, g
from sqlalchemy.orm import selectinload

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/reviews')
def get_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = Review.query.options(selectinload(Review.album)) \
        .order_by(Review.created_at.desc(), Review.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)
    
    output = []
    for review in pagination.items:
        output.append({
            'id': review.id,
            'user_id': review.user_id,
            'album_id': review.album_id,
            'rating': review.rating,
            'review_text': review.review_text or None,
            'created_at': review.created_at,
            'updated_at': review.updated_at or None
        })

    return {"reviews": output,
            "page": pagination.page,
            "total_pages": pagination.pages,
            "total": pagination.total
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