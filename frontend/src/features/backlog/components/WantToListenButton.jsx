import React, { useState } from 'react';
import { useAuth } from '@/context/useAuth.js';
import { useApi } from '@/utils/useApi.js';
import api from '@/api/client.js';

/** Toggle an album on the user's Want to Listen list (the backend's backlog). */
function WantToListenButton({ mbid }) {
    const { isAuthenticated, openLogin } = useAuth()
    const status = useApi(isAuthenticated ? `/backlog/${mbid}/status` : null)
    // Local override after a toggle, keyed by album so it resets on navigation
    const [override, setOverride] = useState({ mbid: null, value: null })
    const [busy, setBusy] = useState(false)

    const inList = override.mbid === mbid ? override.value : !!status.data?.in_backlog

    const toggle = async () => {
        if (!isAuthenticated) return openLogin()
        setBusy(true)
        try {
            await api(`/backlog/${mbid}`, { method: inList ? 'DELETE' : 'POST' })
            setOverride({ mbid, value: !inList })
        } catch {
            window.alert('Could not update Want to Listen. Please try again.')
        } finally {
            setBusy(false)
        }
    }

    return (
        <button
            type='button'
            className={`album-detail-review-btn ${inList ? 'album-detail-review-btn--on' : ''}`}
            onClick={toggle}
            disabled={busy || (isAuthenticated && status.loading)}
            aria-pressed={inList}
        >
            {inList ? '✓ Want to Listen' : '+ Want to Listen'}
        </button>
    )
}

export default WantToListenButton
