from models import Notification, Review, ReviewComment, Album
from db import db
from sqlalchemy.exc import IntegrityError


def create_notification(user_id, actor_id, type_, target_type=None, target_id=None):
    """Create a notification, skipping self-actions and duplicates."""
    if user_id == actor_id:
        return None

    notif = Notification(
        user_id=user_id,
        actor_id=actor_id,
        type=type_,
        target_type=target_type,
        target_id=target_id,
    )
    db.session.add(notif)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return None
    return notif


def _hydrate_target(target_type, target_id):
    if target_type == 'review':
        review = Review.query.get(target_id)
        if not review:
            return None
        album = review.album
        return {
            "kind": "review",
            "id": review.id,
            "album": {
                "mbid": album.mbid,
                "title": album.title,
                "cover_url": album.cover_url,
            },
        }
    if target_type == 'comment':
        comment = ReviewComment.query.get(target_id)
        if not comment:
            return None
        return {
            "kind": "comment",
            "id": comment.id,
            "review_id": comment.review_id,
            "body": comment.body,
        }
    return None


def serialize_notification(notif):
    return {
        "id": notif.id,
        "type": notif.type,
        "read": notif.read,
        "created_at": notif.created_at,
        "actor": {
            "id": notif.actor.id,
            "username": notif.actor.username,
        },
        "target": _hydrate_target(notif.target_type, notif.target_id),
    }
