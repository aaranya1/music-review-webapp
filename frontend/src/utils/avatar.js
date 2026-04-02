/**
 * Parse a '#rrggbb' hex string into { r, g, b } integers.
 * Returns null if the string is missing or malformed.
 */
export function parseHex(hex) {
    if (!hex || hex.length !== 7) return null
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    if (isNaN(r) || isNaN(g) || isNaN(b)) return null
    return { r, g, b }
}

export function getAvatarColor(username) {
    const colors = [
        '#c8a96e', // gold
        '#7eb8a4', // sage
        '#a07eb8', // muted purple
        '#b87e7e', // dusty rose
        '#7e9eb8', // slate blue
        '#b8a07e', // warm tan
        '#7eb87e', // muted green
        '#b8907e', // terracotta
    ];

    let hash = 0;
    for (let i = 0; i < username.length; i++) {
        hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
}