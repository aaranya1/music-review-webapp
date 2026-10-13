import React, { useState } from 'react';
import { useAuth } from '@/context/useAuth.js';
import api from '@/api/client.js';

/**
 * Heart toggle with count. `endpoint` is the like route, e.g. /reviews/5/like.
 * Updates optimistically and settles on the server's count.
 */
function LikeButton({ endpoint, initialLiked, initialCount }) {
    const { isAuthenticated, openLogin } = useAuth()
    const [liked, setLiked] = useState(!!initialLiked)
    const [count, setCount] = useState(initialCount || 0)
    const [busy, setBusy] = useState(false)

    const toggle = async () => {
        if (!isAuthenticated) return openLogin()
        if (busy) return
        const prev = { liked, count }
        setLiked(!liked)
        setCount(count + (liked ? -1 : 1))
        setBusy(true)
        try {
            const res = await api(endpoint, { method: 'POST' })
            setLiked(res.liked)
            setCount(res.like_count)
        } catch {
            setLiked(prev.liked)
            setCount(prev.count)
        } finally {
            setBusy(false)
        }
    }

    return (
        <button
            type='button'
            className={`review-action ${liked ? 'review-action--active' : ''}`}
            onClick={toggle}
            aria-pressed={liked}
            aria-label={liked ? 'Unlike' : 'Like'}
        >
            <span aria-hidden='true'>{liked ? '♥' : '♡'}</span>
            <span>{count}</span>
        </button>
    )
}

export default LikeButton
