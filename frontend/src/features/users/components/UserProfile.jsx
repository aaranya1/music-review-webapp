import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ClipLoader } from 'react-spinners';
import { useAuth } from '@/context/AuthContext.jsx';
import api from '@/api/client.js';
import { getAvatarColor } from '@/utils/avatar.js';
import StarRating from '@/components/ui/StarRating.jsx';
import './UserProfile.css';

function UserProfile() {
    const { user_id } = useParams()
    const { user: currentUser } = useAuth()

    const [profile, setProfile] = useState(null)
    const [reviews, setReviews] = useState([])
    const [profileLoading, setProfileLoading] = useState(true)
    const [reviewsLoading, setReviewsLoading] = useState(true)
    const [error, setError] = useState(null)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [total, setTotal] = useState(0)

    const isOwnProfile = currentUser?.id === parseInt(user_id)

    useEffect(() => {
        setProfileLoading(true)
        api(`/users/${user_id}`)
            .then(data => setProfile(data))
            .catch(err => setError(err.message || 'User not found'))
            .finally(() => setProfileLoading(false))
    }, [user_id])

    useEffect(() => {
        setReviewsLoading(true)
        api(`/users/${user_id}/reviews?page=${page}&per_page=20`)
            .then(data => {
                setReviews(data.reviews || [])
                setTotalPages(data.total_pages || 1)
                setTotal(data.total || 0)
            })
            .catch(() => setReviews([]))
            .finally(() => setReviewsLoading(false))
    }, [user_id, page])

    if (profileLoading) {
        return (
            <div className='profile-loader'>
                <ClipLoader color='#c8a96e' loading size={60} aria-label='Loading' />
            </div>
        )
    }

    if (error) return <div className='profile-error'>{error}</div>
    if (!profile) return null

    const initial = profile.username.charAt(0).toUpperCase()
    const avatarColor = getAvatarColor(profile.username)

    return (
        <div className='profile-root'>

            {/* ── Header ── */}
            <div className='profile-header'>
                <div className='profile-avatar' style={{ borderColor: avatarColor, color: avatarColor }}>{initial}</div>
                <div className='profile-header__info'>
                    <p className='profile-header__label'>
                        {isOwnProfile ? 'Your Profile' : 'Member'}
                    </p>
                    <h1 className='profile-header__username'>{profile.username}</h1>
                    <p className='profile-header__stats'>
                        <span className='profile-header__stat'>
                            <span className='profile-header__stat-value'>{profile.review_count}</span>
                            {' '}{profile.review_count === 1 ? 'review' : 'reviews'}
                        </span>
                    </p>
                </div>
            </div>

            {/* ── Divider ── */}
            <div className='profile-divider'>
                <span className='profile-divider__line' />
                <span className='profile-divider__label'>
                    {isOwnProfile ? 'Your Reviews' : `${profile.username}'s Reviews`}
                </span>
                <span className='profile-divider__line' />
            </div>

            {/* ── Reviews ── */}
            {reviewsLoading ? (
                <div className='profile-reviews-loader'>
                    <ClipLoader color='#c8a96e' loading size={36} />
                </div>
            ) : reviews.length === 0 ? (
                <p className='profile-empty'>
                    {isOwnProfile
                        ? "You haven't reviewed any albums yet."
                        : `${profile.username} hasn't reviewed any albums yet.`}
                </p>
            ) : (
                <>
                    <div className='profile-review-list'>
                        {reviews.map((review, i) => (
                            <Link
                                key={review.id}
                                to={`/albums/${review.mbid}`}
                                className='profile-review-card'
                                style={{ animationDelay: `${i * 35}ms` }}
                            >
                                <div className='profile-review-card__cover-wrap'>
                                    {review.cover_url ? (
                                        <img
                                            src={review.cover_url}
                                            alt={review.album_title}
                                            className='profile-review-card__cover'
                                            onError={(e) => { e.target.src = '/fallback.jpg' }}
                                        />
                                    ) : (
                                        <div className='profile-review-card__cover-fallback'>
                                            {review.album_title?.charAt(0)}
                                        </div>
                                    )}
                                </div>

                                <div className='profile-review-card__body'>
                                    <h3 className='profile-review-card__title'>{review.album_title}</h3>
                                    <div className='profile-review-card__rating'>
                                        <StarRating rating={review.rating} className='profile-star-rating' />
                                        <span className='profile-review-card__rating-val'>
                                            {review.rating.toFixed(1)}
                                        </span>
                                        {review.updated_at && (
                                            <span className='profile-review-card__edited'>edited</span>
                                        )}
                                    </div>
                                    {review.comment && (
                                        <p className='profile-review-card__comment'>{review.comment}</p>
                                    )}
                                </div>
                            </Link>
                        ))}
                    </div>

                    {/* ── Pagination ── */}
                    {totalPages > 1 && (
                        <div className='profile-pagination'>
                            <button
                                onClick={() => setPage(p => p - 1)}
                                disabled={page === 1}
                            >← Prev</button>
                            <span className='profile-pagination__label'>{page} / {totalPages}</span>
                            <button
                                onClick={() => setPage(p => p + 1)}
                                disabled={page === totalPages}
                            >Next →</button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default UserProfile