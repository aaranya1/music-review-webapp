import React, { useState } from 'react';
import LikeButton from './LikeButton.jsx';
import CommentThread from './CommentThread.jsx';
import './ReviewActions.css';

/** Like + comments row for a review (shape from serialize_review). */
function ReviewActions({ review }) {
    const [open, setOpen] = useState(false)
    const [commentCount, setCommentCount] = useState(review.comment_count || 0)

    return (
        <div className='review-actions'>
            <div className='review-actions__row'>
                <LikeButton
                    endpoint={`/reviews/${review.id}/like`}
                    initialLiked={review.liked_by_me}
                    initialCount={review.like_count}
                />
                <button
                    type='button'
                    className={`review-action ${open ? 'review-action--active' : ''}`}
                    onClick={() => setOpen(o => !o)}
                    aria-expanded={open}
                >
                    <span aria-hidden='true'>💬</span>
                    <span>{commentCount}</span>
                </button>
            </div>
            {open && (
                <CommentThread
                    reviewId={review.id}
                    onCountChange={delta => setCommentCount(n => n + delta)}
                />
            )}
        </div>
    )
}

export default ReviewActions
