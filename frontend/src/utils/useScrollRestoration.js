import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Saves the scroll position to sessionStorage on unmount and restores it on
 * mount. Use this in paginated list pages so back-navigation lands where the
 * user left off.
 */
export function useScrollRestoration() {
    const { pathname, search } = useLocation()
    const key = `scroll:${pathname}${search}`

    useEffect(() => {
        const saved = sessionStorage.getItem(key)
        if (saved !== null) {
            window.scrollTo(0, parseInt(saved, 10))
        }
        return () => {
            sessionStorage.setItem(key, String(Math.round(window.scrollY)))
        }
    }, [key])
}
