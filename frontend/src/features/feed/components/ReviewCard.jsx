import React from 'react';
import { Link } from 'react-router-dom';
import StarRating from '@/components/ui/StarRating.jsx';
import ReviewActions from '@/features/reviews/components/ReviewActions.jsx';
import { getAvatarColor } from '@/utils/avatar.js';
import { timeAgo } from '@/utils/time.js';

/** A review with its album, for the feed (shape from serialize_review). */
function ReviewCard({ review }) {
    const { album } = review
    const userColor = getAvatarColor(review.username)

    return (
        <article className='review-card'>
            <Link to={`/albums/${album.mbid}`} className='review-card__cover-link'>
                {album.cover_url ? (
                    <img src={album.cover_url} alt={album.title} className='review-card__cover' loading='lazy' />
                ) : (
                    <div className='review-card__cover review-card__cover--fallback'>{album.title.charAt(0)}</div>
                )}
            </Link>

            <div className='review-card__body'>
                <div className='review-card__album'>
                    <Link to={`/albums/${album.mbid}`} className='review-card__title'>{album.title}</Link>
                    {album.release_year && <span className='review-card__year'>{album.release_year}</span>}
                </div>
                <p className='review-card__artists'>
                    {album.artists.map((a, i) => (
                        <React.Fragment key={a.mbid}>
                            <Link to={`/artists/${a.mbid}`}>{a.name}</Link>
                            {i < album.artists.length - 1 && ', '}
                        </React.Fragment>
                    ))}
                </p>

                <div className='review-card__meta'>
                    <Link to={`/users/${review.user_id}`} className='review-card__user' style={{ color: userColor }}>
                        {review.username}
                    </Link>
                    <StarRating rating={review.rating} />
                    <span className='review-card__time'>{timeAgo(review.created_at)}</span>
                </div>

                {review.review_text && <p className='review-card__text'>{review.review_text}</p>}

                <ReviewActions review={review} />
            </div>
        </article>
    )
}

export default ReviewCard
