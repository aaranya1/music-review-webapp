const UNITS = [
    ['y', 365 * 24 * 3600],
    ['mo', 30 * 24 * 3600],
    ['w', 7 * 24 * 3600],
    ['d', 24 * 3600],
    ['h', 3600],
    ['m', 60],
]

/**
 * Short relative time like "2h" or "3d" for an ISO timestamp.
 * The API sends naive UTC timestamps, so treat a missing offset as UTC.
 */
export function timeAgo(iso) {
    if (!iso) return ''
    const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(iso)
    const then = new Date(hasZone ? iso : `${iso}Z`).getTime()
    const seconds = Math.max(0, (Date.now() - then) / 1000)
    for (const [label, size] of UNITS) {
        if (seconds >= size) return `${Math.floor(seconds / size)}${label}`
    }
    return 'now'
}
