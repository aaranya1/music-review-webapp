import { useCallback, useEffect, useState } from 'react';
import api from '@/api/client.js';

/**
 * Fetch `url` with the API client and track its state.
 *
 * - State is only set from the request's callbacks (never synchronously in the
 *   effect), and responses for a URL the component has moved away from are
 *   ignored, so fast pagination can't show a stale page.
 * - `data` stays available while the same URL is being reloaded, so callers can
 *   refresh without flashing a skeleton. It's null once the URL changes.
 * - Pass a null url to skip fetching.
 *
 * Returns { data, error, loading, reload }.
 */
export function useApi(url) {
    const [nonce, setNonce] = useState(0)
    const [result, setResult] = useState({ url: null, nonce: -1, data: null, error: null })

    useEffect(() => {
        if (url == null) return
        let cancelled = false
        api(url)
            .then(data => {
                if (!cancelled) setResult({ url, nonce, data, error: null })
            })
            .catch(err => {
                if (!cancelled) setResult({ url, nonce, data: null, error: err.message || 'Request failed' })
            })
        return () => { cancelled = true }
    }, [url, nonce])

    const reload = useCallback(() => setNonce(n => n + 1), [])

    const sameUrl = result.url === url
    const current = sameUrl && result.nonce === nonce
    return {
        data: sameUrl ? result.data : null,
        // Hide a previous error while a retry is in flight
        error: current ? result.error : null,
        loading: url != null && !current,
        reload,
    }
}
