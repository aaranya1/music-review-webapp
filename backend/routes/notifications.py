from flask import Blueprint, request, g
from models import Notification
from db import db
from routes.auth import token_required
from notifications_service import serialize_notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = (
        Notification.query
        .filter_by(user_id=g.user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return {
        "notifications": [serialize_notification(n) for n in pagination.items],
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
    }


@notifications_bp.route('/notifications/unread-count', methods=['GET'])
@token_required
def unread_count():
    count = Notification.query.filter_by(user_id=g.user_id, read=False).count()
    return {"unread_count": count}


@notifications_bp.route('/notifications/<int:notif_id>/read', methods=['PUT'])
@token_required
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=g.user_id).first_or_404()
    notif.read = True
    db.session.commit()
    return {"message": "Marked as read"}, 200


@notifications_bp.route('/notifications/read-all', methods=['PUT'])
@token_required
def mark_all_read():
    Notification.query.filter_by(user_id=g.user_id, read=False).update({"read": True})
    db.session.commit()
    return {"message": "All marked as read"}, 200


@notifications_bp.route('/notifications/<int:notif_id>', methods=['DELETE'])
@token_required
def delete_notification(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=g.user_id).first_or_404()
    db.session.delete(notif)
    db.session.commit()
    return {"message": "Deleted"}, 200
