import React from 'react';

function StarRating({ rating, max = 5, className = 'star-rating' }) {
    const fullStars = Math.floor(rating)
    const hasHalf = rating % 1 >= 0.5
    const emptyStars = max - fullStars - (hasHalf ? 1 : 0)
    return (
        <span className={className}>
            {'★'.repeat(fullStars)}
            {hasHalf && '½'}
            {'☆'.repeat(emptyStars)}
        </span>
    )
}

export default StarRating
