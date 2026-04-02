from flask import Blueprint
from models import Review

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    latest_reviews = (
        Review.query
        .order_by(Review.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "latest_reviews": [
            {
                "album": review.album.title,
                "artist": review.album.artists[0].name if review.album.artists else None,
                "rating": review.rating,
                "comment": review.review_text,
                "username": review.user.username
            }
            for review in latest_reviews
        ]
    }