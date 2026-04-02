import React, { useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { useAuth } from '../../context/AuthContext.jsx';
import { Link } from 'react-router-dom';
import { getAvatarColor } from '../../utils/avatar.js';
import api from '../../api/client.js';
import './ReviewList.css';

function StarPicker({ value, onChange }) {
    const [hovered, setHovered] = useState(null)

    return (
        <div className='star-picker'>
            {[1, 2, 3, 4, 5].map(star => {
                const active = hovered !== null ? hovered : value
                const full = active >= star
                const half = !full && active >= star - 0.5
                return (
                    <span
                        key={star}
                        className='star-picker__star'
                        onMouseMove={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect()
                            const isLeft = e.clientX - rect.left < rect.width / 2
                            setHovered(isLeft ? star - 0.5 : star)
                        }}
                        onMouseLeave={() => setHovered(null)}
                        onClick={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect()
                            const isLeft = e.clientX - rect.left < rect.width / 2
                            onChange(isLeft ? star - 0.5 : star)
                        }}
                    >
                        <span className={`star-picker__fill ${full ? 'full' : half ? 'half' : 'empty'}`}>★</span>
                    </span>
                )
            })}
            {value > 0 && <span className='star-picker__value'>{value.toFixed(1)}</span>}
        </div>
    )
}

function StarRating({ rating }) {
    const fullStars = Math.floor(rating)
    const hasHalf = rating % 1 >= 0.5
    const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0)
    return (
        <span className='star-rating'>
            {'★'.repeat(fullStars)}
            {hasHalf && '½'}
            {'☆'.repeat(emptyStars)}
        </span>
    )
}

function ReviewItem({ review, currentUser, onUpdated, onDeleted }) {
    const [editing, setEditing] = useState(false)
    const [editRating, setEditRating] = useState(review.rating)
    const [editText, setEditText] = useState(review.comment || '')
    const [saving, setSaving] = useState(false)

    const isOwn = review.username === currentUser?.username

    const handleSave = async () => {
        setSaving(true)
        try {
            await api(`/reviews/${review.id}`, {
                method: 'PUT',
                body: { rating: editRating, review_text: editText }
            })
            setEditing(false)
            onUpdated()
        } catch (err) {
            // keep edit open
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async () => {
        if (!window.confirm('Delete your review?')) return
        try {
            await api(`/reviews/${review.id}`, { method: 'DELETE' })
            onDeleted()
        } catch (err) {}
    }

    const handleCancel = () => {
        setEditing(false)
        setEditRating(review.rating)
        setEditText(review.comment || '')
    }

    const usernameColor = getAvatarColor(review.username)
    return (
        <div className={`review-item ${isOwn ? 'review-item--own' : ''}`}>
            {editing ? (
                <div className='review-item__edit'>
                    <StarPicker value={editRating} onChange={setEditRating} />
                    <textarea
                        className='review-item__textarea'
                        value={editText}
                        onChange={e => setEditText(e.target.value)}
                        disabled={saving}
                        rows={3}
                    />
                    <div className='review-item__edit-actions'>
                        <button
                            className='review-item__save-btn'
                            onClick={handleSave}
                            disabled={saving || editRating === 0}
                        >
                            {saving ? 'Saving…' : 'Save'}
                        </button>
                        <button className='review-item__cancel-btn' onClick={handleCancel}>
                            Cancel
                        </button>
                    </div>
                </div>
            ) : (
                <>
                    <div className='review-item__header'>
                        <Link to={`/users/${review.user_id}`} className='review-item__username' style={{ borderColor: usernameColor, color: usernameColor }}>{review.username}</Link>
                        <span className='review-item__stars'><StarRating rating={review.rating} /></span>
                        <span className='review-item__rating-val'>{review.rating.toFixed(1)}</span>
                        {review.updated_at && (
                            <span className='review-item__edited'>edited</span>
                        )}
                    </div>
                    {review.comment && (
                        <p className='review-item__comment'>{review.comment}</p>
                    )}
                    {isOwn && (
                        <div className='review-item__actions'>
                            <button className='review-item__edit-btn' onClick={() => setEditing(true)}>Edit</button>
                            <button className='review-item__delete-btn' onClick={handleDelete}>Delete</button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

function ReviewList({ reviews, loading, onUpdated, onDeleted }) {
    const { user } = useAuth()

    if (loading) {
        return (
            <div className='review-list__loader'>
                <ClipLoader color='#c8a96e' loading size={30} />
            </div>
        )
    }

    if (reviews.length === 0) {
        return <p className='review-list__empty'>Be the first to review this album.</p>
    }

    return (
        <div className='review-list'>
            {reviews.map(review => (
                <ReviewItem
                    key={review.id}
                    review={review}
                    currentUser={user}
                    onUpdated={onUpdated}
                    onDeleted={onDeleted}
                />
            ))}
        </div>
    )
}

export default ReviewList