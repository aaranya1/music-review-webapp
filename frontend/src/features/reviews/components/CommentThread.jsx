import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/useAuth.js';
import { useApi } from '@/utils/useApi.js';
import { timeAgo } from '@/utils/time.js';
import api from '@/api/client.js';
import LikeButton from './LikeButton.jsx';

const BODY_MAX = 2000

function CommentThread({ reviewId, onCountChange }) {
    const { user, isAuthenticated, openLogin } = useAuth()
    const { data, error, loading, reload } = useApi(`/reviews/${reviewId}/comments`)
    const [body, setBody] = useState('')
    const [posting, setPosting] = useState(false)
    const [postError, setPostError] = useState(null)

    const comments = data?.comments || []

    const submit = async (e) => {
        e.preventDefault()
        if (!body.trim() || posting) return
        setPosting(true)
        setPostError(null)
        try {
            await api(`/reviews/${reviewId}/comments`, { method: 'POST', body: { body } })
            setBody('')
            reload()
            onCountChange?.(1)
        } catch (err) {
            setPostError(err.message || 'Could not post the comment.')
        } finally {
            setPosting(false)
        }
    }

    const remove = async (commentId) => {
        if (!window.confirm('Delete this comment?')) return
        try {
            await api(`/reviews/${reviewId}/comments/${commentId}`, { method: 'DELETE' })
            reload()
            onCountChange?.(-1)
        } catch {
            window.alert('Could not delete the comment. Please try again.')
        }
    }

    return (
        <div className='comment-thread'>
            {loading && !data && <p className='comment-thread__status'>Loading comments…</p>}
            {error && <p className='comment-thread__status'>Couldn't load comments.</p>}

            {comments.map(c => (
                <div key={c.id} className='comment'>
                    <div className='comment__meta'>
                        <Link to={`/users/${c.user_id}`} className='comment__author'>{c.username}</Link>
                        <span className='comment__time'>{timeAgo(c.created_at)}</span>
                    </div>
                    <p className='comment__body'>{c.body}</p>
                    <div className='comment__actions'>
                        <LikeButton
                            endpoint={`/reviews/${reviewId}/comments/${c.id}/like`}
                            initialLiked={c.liked_by_me}
                            initialCount={c.like_count}
                        />
                        {user?.id === c.user_id && (
                            <button type='button' className='comment__delete' onClick={() => remove(c.id)}>
                                Delete
                            </button>
                        )}
                    </div>
                </div>
            ))}

            {!loading && !error && comments.length === 0 && (
                <p className='comment-thread__status'>No comments yet.</p>
            )}

            {isAuthenticated ? (
                <form className='comment-form' onSubmit={submit}>
                    <textarea
                        className='comment-form__input'
                        placeholder='Add a comment…'
                        value={body}
                        maxLength={BODY_MAX}
                        rows={2}
                        onChange={e => setBody(e.target.value)}
                    />
                    <div className='comment-form__row'>
                        {postError && <span className='comment-form__error'>{postError}</span>}
                        <button type='submit' className='comment-form__submit' disabled={!body.trim() || posting}>
                            {posting ? 'Posting…' : 'Post'}
                        </button>
                    </div>
                </form>
            ) : (
                <button type='button' className='comment-thread__login' onClick={openLogin}>
                    Log in to comment
                </button>
            )}
        </div>
    )
}

export default CommentThread
