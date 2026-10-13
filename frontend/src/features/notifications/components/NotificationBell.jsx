import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useApi } from '@/utils/useApi.js';
import api from '@/api/client.js';
import NotificationItem from './NotificationItem.jsx';
import './Notifications.css';

const POLL_MS = 60_000

/** Navbar bell: unread badge (polled) and a dropdown of the latest notifications. */
function NotificationBell() {
    const [open, setOpen] = useState(false)
    const wrapRef = useRef(null)

    const unread = useApi('/notifications/unread-count')
    const latest = useApi(open ? '/notifications?per_page=10' : null)
    const count = unread.data?.unread_count || 0
    const { reload: reloadCount } = unread

    useEffect(() => {
        const id = setInterval(reloadCount, POLL_MS)
        return () => clearInterval(id)
    }, [reloadCount])

    useEffect(() => {
        if (!open) return
        const onClick = (e) => {
            if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
        }
        const onKey = (e) => { if (e.key === 'Escape') setOpen(false) }
        document.addEventListener('mousedown', onClick)
        window.addEventListener('keydown', onKey)
        return () => {
            document.removeEventListener('mousedown', onClick)
            window.removeEventListener('keydown', onKey)
        }
    }, [open])

    const markOneRead = (n) => {
        setOpen(false)
        if (!n.read) api(`/notifications/${n.id}/read`, { method: 'PUT' }).then(reloadCount).catch(() => {})
    }

    const markAllRead = async () => {
        try {
            await api('/notifications/read-all', { method: 'PUT' })
            reloadCount()
            latest.reload()
        } catch {
            // leave as-is; the badge will catch up on the next poll
        }
    }

    const items = latest.data?.notifications || []

    return (
        <div className='notif-bell' ref={wrapRef}>
            <button
                type='button'
                className='notif-bell__button'
                onClick={() => setOpen(o => !o)}
                aria-label={count ? `Notifications, ${count} unread` : 'Notifications'}
                aria-expanded={open}
            >
                <svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round' aria-hidden='true'>
                    <path d='M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9' />
                    <path d='M13.73 21a2 2 0 0 1-3.46 0' />
                </svg>
                {count > 0 && <span className='notif-bell__badge'>{count > 99 ? '99+' : count}</span>}
            </button>

            {open && (
                <div className='notif-panel'>
                    <div className='notif-panel__list'>
                        {latest.loading && !latest.data && <p className='notif-panel__status'>Loading…</p>}
                        {latest.error && <p className='notif-panel__status'>Couldn't load notifications.</p>}
                        {latest.data && items.length === 0 && <p className='notif-panel__status'>Nothing yet.</p>}
                        {items.map(n => <NotificationItem key={n.id} notification={n} onOpen={markOneRead} />)}
                    </div>
                    <div className='notif-panel__footer'>
                        <button type='button' className='notif-panel__action' onClick={markAllRead} disabled={count === 0}>
                            Mark all read
                        </button>
                        <Link to='/notifications' className='notif-panel__action' onClick={() => setOpen(false)}>
                            See all →
                        </Link>
                    </div>
                </div>
            )}
        </div>
    )
}

export default NotificationBell
