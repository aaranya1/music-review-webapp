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
        "album": {
            "mbid": album.mbid,
            "title": album.title,
            "cover_url": album.cover_url,
            "release_year": album.release_date.year if album.release_date else None,
            "artists": [{"mbid": a.mbid, "name": a.name} for a in album.artists],
        }
    }
