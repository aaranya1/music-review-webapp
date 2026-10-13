import React, { useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { useAuth } from '@/context/useAuth.js';
import { useApi } from '@/utils/useApi.js';
import api from '@/api/client.js';
import NotificationItem from './NotificationItem.jsx';
import './Notifications.css';

function NotificationsList() {
    const [page, setPage] = useState(1)
    const { data, error, loading, reload } = useApi(`/notifications?page=${page}&per_page=20`)
    const items = data?.notifications || []
    const totalPages = data?.total_pages || 1

    const markOneRead = (n) => {
        if (!n.read) api(`/notifications/${n.id}/read`, { method: 'PUT' }).catch(() => {})
    }

    const markAllRead = async () => {
        try {
            await api('/notifications/read-all', { method: 'PUT' })
            reload()
        } catch {
            window.alert('Could not mark notifications as read. Please try again.')
        }
    }

    return (
        <>
            <div className='notif-page__header'>
                <h2 className='notif-page__title'>Notifications</h2>
                {items.some(n => !n.read) && (
                    <button type='button' className='notif-panel__action' onClick={markAllRead}>Mark all read</button>
                )}
            </div>

            {loading && !data && (
                <div className='notif-page__loader'><ClipLoader color='#c8a96e' size={32} aria-label='Loading' /></div>
            )}
            {error && <p className='notif-panel__status'>Couldn't load notifications.</p>}
            {data && items.length === 0 && (
                <p className='notif-panel__status'>
                    Nothing yet. You'll hear about likes, comments, and new followers here.
                </p>
            )}

            <div className='notif-page__list'>
                {items.map(n => <NotificationItem key={n.id} notification={n} onOpen={markOneRead} />)}
            </div>

            {totalPages > 1 && (
                <div className='pagination'>
                    <button onClick={() => setPage(p => p - 1)} disabled={page === 1}>← Prev</button>
                    <span className='page-label'>{page} / {totalPages}</span>
                    <button onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>Next →</button>
                </div>
            )}
        </>
    )
}

function NotificationsPage() {
    const { isAuthenticated, openLogin } = useAuth()

    return (
        <div className='notif-page'>
            {isAuthenticated ? <NotificationsList /> : (
                <p className='notif-panel__status'>
                    <button type='button' className='feed__link' onClick={openLogin}>Log in</button> to see your notifications.
                </p>
            )}
        </div>
    )
}

export default NotificationsPage
