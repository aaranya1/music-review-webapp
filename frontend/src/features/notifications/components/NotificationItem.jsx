import React from 'react';
import { Link } from 'react-router-dom';
import { timeAgo } from '@/utils/time.js';

/** Sentence and link for a notification (shape from serialize_notification). */
function describeNotification(n) {
    const album = n.target?.album
    const albumTitle = album?.title || 'an album'
    switch (n.type) {
        case 'review_like':
            return { text: <>liked your review of <em>{albumTitle}</em></>, to: album ? `/albums/${album.mbid}` : null }
        case 'new_comment':
            return {
                text: <>commented on your review of <em>{albumTitle}</em>{n.target?.body ? `: “${n.target.body}”` : ''}</>,
                to: album ? `/albums/${album.mbid}` : null,
            }
        case 'comment_like':
            return { text: <>liked your comment on <em>{albumTitle}</em></>, to: album ? `/albums/${album.mbid}` : null }
        case 'new_follower':
            return { text: 'followed you', to: `/users/${n.actor.id}` }
        default:
            return { text: 'sent you a notification', to: null }
    }
}

function NotificationItem({ notification, onOpen }) {
    const { text, to } = describeNotification(notification)
    // The target can be gone (deleted review); fall back to the actor's profile
    const href = to || `/users/${notification.actor.id}`

    return (
        <Link
            to={href}
            className={`notification ${notification.read ? '' : 'notification--unread'}`}
            onClick={() => onOpen?.(notification)}
        >
            <span className='notification__text'>
                <strong className='notification__actor'>{notification.actor.username}</strong> {text}
            </span>
            <span className='notification__time'>{timeAgo(notification.created_at)}</span>
        </Link>
    )
}

export default NotificationItem
