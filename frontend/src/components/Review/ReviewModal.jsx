import React, { useState, useEffect } from 'react';
import api from '../../api/client.js';
import './ReviewModal.css';

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

function ReviewModal({ mbid, albumTitle, onClose, onSubmitted }) {
    const [rating, setRating] = useState(0)
    const [reviewText, setReviewText] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState(null)

    // Close on Escape key
    useEffect(() => {
        const handleKey = (e) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [onClose])

    // Prevent body scroll while modal is open
    useEffect(() => {
        document.body.style.overflow = 'hidden'
        return () => { document.body.style.overflow = '' }
    }, [])

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) onClose()
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (rating === 0) { 
            setError('Please select a rating.') 
            return 
        }
        setSubmitting(true)
        setError(null)
        try {
            await api(`/albums/${mbid}/reviews`, {
                method: 'POST',
                body: { rating, review_text: reviewText }
            })
            onSubmitted()
            onClose()
        } catch (err) {
            setError(err.message || 'Failed to submit review.')
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div className='modal-backdrop' onClick={handleBackdropClick}>
            <div className='modal'>
                <button className='modal__close' onClick={onClose} aria-label='Close'>✕</button>

                <p className='modal__label'>Review</p>
                <h2 className='modal__title'>{albumTitle}</h2>

                <div className='modal__divider' />

                <form onSubmit={handleSubmit}>
                    <p className='modal__field-label'>Your Rating</p>
                    <StarPicker value={rating} onChange={setRating} />

                    <p className='modal__field-label'>Your Thoughts <span className='modal__optional'>(optional)</span></p>
                    <textarea
                        className='modal__textarea'
                        placeholder='What did you think of this album?'
                        value={reviewText}
                        onChange={e => setReviewText(e.target.value)}
                        disabled={submitting}
                        rows={4}
                    />

                    {error && <p className='modal__error'>{error}</p>}

                    <div className='modal__actions'>
                        <button type='button' className='modal__cancel' onClick={onClose}>
                            Cancel
                        </button>
                        <button
                            type='submit'
                            className='modal__submit'
                            disabled={submitting || rating === 0}
                        >
                            {submitting ? 'Submitting…' : 'Submit Review'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default ReviewModal