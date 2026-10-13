from sqlalchemy.orm import selectinload
from models import Review


def review_load_options():
    """Eager-load everything serialize_review touches, to avoid per-review queries."""
    return (
        selectinload(Review.user),
        selectinload(Review.album),
        selectinload(Review.likes),
        selectinload(Review.comments),
    )


def serialize_review(review):
    album = review.album
    return {
        "id": review.id,
        "user_id": review.user_id,
        "username": review.user.username,
        "rating": review.rating,
        "review_text": review.review_text or None,
        "created_at": review.created_at,
        "updated_at": review.updated_at or None,
        "like_count": len(review.likes),
        "comment_count": len(review.comments),
        "album": {
            "mbid": album.mbid,
            "title": album.title,
            "cover_url": album.cover_url,
            "release_year": album.release_date.year if album.release_date else None,
            "artists": [{"mbid": a.mbid, "name": a.name} for a in album.artists],
        }
    }
