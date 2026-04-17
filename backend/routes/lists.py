from flask import Blueprint, request, g
from models import List, ListItem, Album
from db import db
from routes.auth import token_required
from sqlalchemy.orm import selectinload

lists_bp = Blueprint('lists', __name__)


def _serialize_list(lst, include_items=False):
    data = {
        "id": lst.id,
        "user_id": lst.user_id,
        "username": lst.user.username,
        "title": lst.title,
        "description": lst.description or None,
        "is_public": lst.is_public,
        "item_count": len(lst.items),
        "preview_covers": [
            item.album.cover_url
            for item in lst.items[:4]
            if item.album.cover_url
        ],
        "created_at": lst.created_at,
        "updated_at": lst.updated_at or None,
    }
    if include_items:
        data["items"] = [
            {
                "id": item.id,
                "position": item.position,
                "note": item.note or None,
                "album": {
                    "id": item.album.id,
                    "mbid": item.album.mbid,
                    "title": item.album.title,
                    "cover_url": item.album.cover_url,
                    "release_year": item.album.release_date.year if item.album.release_date else None,
                    "artists": [{"mbid": a.mbid, "name": a.name} for a in item.album.artists],
                }
            }
            for item in lst.items
        ]
    return data


# ── Browse public lists ───────────────────────────────────────────────────────

@lists_bp.route('/lists', methods=['GET'])
def get_lists():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = (
        List.query
        .filter_by(is_public=True)
        .options(selectinload(List.items).selectinload(ListItem.album).selectinload(Album.artists),
                 selectinload(List.user))
        .order_by(List.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return {
        "lists": [_serialize_list(lst) for lst in pagination.items],
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
    }


# ── Create a list ─────────────────────────────────────────────────────────────

@lists_bp.route('/lists', methods=['POST'])
@token_required
def create_list():
    data = request.get_json()
    title = (data.get('title') or '').strip()
    if not title:
        return {"message": "Title is required"}, 400

    lst = List(
        user_id=g.user_id,
        title=title,
        description=data.get('description'),
        is_public=data.get('is_public', True),
    )
    db.session.add(lst)
    db.session.commit()
    return {"message": "List created", "id": lst.id}, 201


# ── Get a single list ─────────────────────────────────────────────────────────

@lists_bp.route('/lists/<int:list_id>', methods=['GET'])
def get_list(list_id):
    lst = (
        List.query
        .options(selectinload(List.items).selectinload(ListItem.album).selectinload(Album.artists),
                 selectinload(List.user))
        .filter_by(id=list_id)
        .first_or_404()
    )
    if not lst.is_public and lst.user_id != getattr(g, 'user_id', None):
        return {"message": "Not found"}, 404
    return _serialize_list(lst, include_items=True)


# ── Update list metadata ──────────────────────────────────────────────────────

@lists_bp.route('/lists/<int:list_id>', methods=['PUT'])
@token_required
def update_list(list_id):
    lst = List.query.filter_by(id=list_id).first_or_404()
    if lst.user_id != g.user_id:
        return {"message": "Unauthorized"}, 403

    data = request.get_json()
    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return {"message": "Title cannot be empty"}, 400
        lst.title = title
    if 'description' in data:
        lst.description = data['description']
    if 'is_public' in data:
        lst.is_public = bool(data['is_public'])

    lst.updated_at = db.func.current_timestamp()
    db.session.commit()
    return {"message": "List updated"}, 200


# ── Delete a list ─────────────────────────────────────────────────────────────

@lists_bp.route('/lists/<int:list_id>', methods=['DELETE'])
@token_required
def delete_list(list_id):
    lst = List.query.filter_by(id=list_id).first_or_404()
    if lst.user_id != g.user_id:
        return {"message": "Unauthorized"}, 403
    db.session.delete(lst)
    db.session.commit()
    return {"message": "List deleted"}, 200


# ── Add album to list ─────────────────────────────────────────────────────────

@lists_bp.route('/lists/<int:list_id>/items', methods=['POST'])
@token_required
def add_item(list_id):
    lst = List.query.filter_by(id=list_id).first_or_404()
    if lst.user_id != g.user_id:
        return {"message": "Unauthorized"}, 403

    data = request.get_json()
    album_mbid = data.get('album_mbid')
    if not album_mbid:
        return {"message": "album_mbid is required"}, 400

    album = Album.query.filter_by(mbid=album_mbid).first_or_404()

    if ListItem.query.filter_by(list_id=list_id, album_id=album.id).first():
        return {"message": "Album already in list"}, 409

    max_pos = db.session.query(db.func.max(ListItem.position)).filter_by(list_id=list_id).scalar() or 0
    item = ListItem(
        list_id=list_id,
        album_id=album.id,
        position=max_pos + 1,
        note=data.get('note'),
    )
    db.session.add(item)
    lst.updated_at = db.func.current_timestamp()
    db.session.commit()
    return {"message": "Album added", "id": item.id}, 201


# ── Remove album from list ────────────────────────────────────────────────────

@lists_bp.route('/lists/<int:list_id>/items/<int:item_id>', methods=['DELETE'])
@token_required
def remove_item(list_id, item_id):
    lst = List.query.filter_by(id=list_id).first_or_404()
    if lst.user_id != g.user_id:
        return {"message": "Unauthorized"}, 403

    item = ListItem.query.filter_by(id=item_id, list_id=list_id).first_or_404()
    db.session.delete(item)
    lst.updated_at = db.func.current_timestamp()
    db.session.commit()
    return {"message": "Album removed"}, 200


# ── Reorder items ─────────────────────────────────────────────────────────────

@lists_bp.route('/lists/<int:list_id>/items/reorder', methods=['PUT'])
@token_required
def reorder_items(list_id):
    lst = List.query.filter_by(id=list_id).first_or_404()
    if lst.user_id != g.user_id:
        return {"message": "Unauthorized"}, 403

    # Expects: {"order": [item_id, item_id, ...]} in desired position order
    data = request.get_json()
    order = data.get('order', [])
    if not isinstance(order, list):
        return {"message": "order must be a list of item IDs"}, 400

    items = {item.id: item for item in lst.items}
    if set(order) != set(items.keys()):
        return {"message": "order must contain every item ID exactly once"}, 400

    for position, item_id in enumerate(order, start=1):
        items[item_id].position = position

    lst.updated_at = db.func.current_timestamp()
    db.session.commit()
    return {"message": "Order updated"}, 200


# ── User's lists ──────────────────────────────────────────────────────────────

@lists_bp.route('/users/<int:user_id>/lists', methods=['GET'])
def get_user_lists(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    query = List.query.filter_by(user_id=user_id)
    # Only show private lists to the owner
    if getattr(g, 'user_id', None) != user_id:
        query = query.filter_by(is_public=True)

    pagination = (
        query
        .options(selectinload(List.items).selectinload(ListItem.album).selectinload(Album.artists),
                 selectinload(List.user))
        .order_by(List.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return {
        "lists": [_serialize_list(lst) for lst in pagination.items],
        "page": pagination.page,
        "total_pages": pagination.pages,
        "total": pagination.total,
    }
