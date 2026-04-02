import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import api from '../../api/client.js';
import ReviewModal from '../Review/ReviewModal.jsx';
import ReviewList from '../Review/ReviewList.jsx';
import { AlbumDetailSkeleton } from '../Skeleton.jsx';
import { parseHex } from '../../utils/avatar.js';
import './AlbumDetails.css';

function formatDuration(ms) {
    if (!ms) return null
    const totalSeconds = Math.floor(ms / 1000)
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

function StarRating({ rating, max = 5 }) {
    const fullStars = Math.floor(rating)
    const hasHalf = rating % 1 >= 0.5
    const emptyStars = max - fullStars - (hasHalf ? 1 : 0)
    return (
        <span className='star-rating'>
            {'★'.repeat(fullStars)}
            {hasHalf && '½'}
            {'☆'.repeat(emptyStars)}
        </span>
    )
}

// ── Cover lightbox ──────────────────────────────────────────────────────────
function CoverLightbox({ src, alt, onClose }) {
    useEffect(() => {
        const handleKey = e => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', handleKey)
        document.body.style.overflow = 'hidden'
        return () => {
            window.removeEventListener('keydown', handleKey)
            document.body.style.overflow = ''
        }
    }, [onClose])

    return (
        <div className='lightbox-backdrop' onClick={onClose}>
            <img
                src={src}
                alt={alt}
                className='lightbox-img'
                onClick={e => e.stopPropagation()}
            />
            <button className='lightbox-close' onClick={onClose} aria-label='Close'>✕</button>
        </div>
    )
}

// ── Track row with expandable credits drawer ─────────────────────────────────
function TrackRow({ track, albumArtists = [] }) {
    const [open, setOpen] = useState(false)

    const hasCredits = track.credits && track.credits.length > 0

    // Merge album-level artists with track-level artists, deduplicated by mbid
    const allArtists = [
        ...albumArtists,
        ...(track.artists || []).filter(a => !albumArtists.some(aa => aa.mbid === a.mbid))
    ]

    // Group credits by role for display
    const creditsByRole = hasCredits
        ? track.credits.reduce((acc, credit) => {
            const role = credit.role.charAt(0).toUpperCase() + credit.role.slice(1)
            if (!acc[role]) acc[role] = []
            acc[role].push(credit.artist_name)
            return acc
        }, {})
        : {}

    return (
        <>
            <tr
                className={`album-detail-track ${open ? 'album-detail-track--open' : ''}`}
                onClick={() => setOpen(o => !o)}
            >
                <td className='album-detail-track__num'>{track.track_number}</td>
                <td className='album-detail-track__title'>
                    <span className='album-detail-track__title-text'>{track.title}</span>
                    {allArtists.length > 0 && (
                        <span className='album-detail-track__artists'>
                            {allArtists.map((artist, i) => (
                                <span key={artist.mbid}>
                                    <Link
                                        to={`/artists/${artist.mbid}`}
                                        onClick={e => e.stopPropagation()}
                                    >
                                        {artist.name}
                                    </Link>
                                    {i < allArtists.length - 1 && ', '}
                                </span>
                            ))}
                        </span>
                    )}
                </td>
                <td className='album-detail-track__duration'>
                    {formatDuration(track.duration_ms)}
                </td>
                <td className='album-detail-track__chevron'>
                    <svg
                        width='10'
                        height='10'
                        viewBox='0 0 10 10'
                        className={`chevron ${open ? 'chevron--open' : ''}`}
                    >
                        <polyline points='1,3 5,7 9,3' fill='none' stroke='currentColor' strokeWidth='1.5' strokeLinecap='round' strokeLinejoin='round' />
                    </svg>
                </td>
            </tr>

            {open && (
                <tr className='album-detail-track-credits'>
                    <td colSpan={4}>
                        <div className='track-credits-drawer'>
                            {!hasCredits ? (
                                <p className='track-credits-drawer__empty'>
                                    No credits available for this track.
                                </p>
                            ) : (
                                <dl className='track-credits-list'>
                                    {Object.entries(creditsByRole).map(([role, names]) => (
                                        <div key={role} className='track-credits-list__row'>
                                            <dt className='track-credits-list__role'>{role}</dt>
                                            <dd className='track-credits-list__names'>
                                                {names.join(', ')}
                                            </dd>
                                        </div>
                                    ))}
                                </dl>
                            )}
                        </div>
                    </td>
                </tr>
            )}
        </>
    )
}

// ── Rating distribution histogram ────────────────────────────────────────────
function RatingDistribution({ reviews, accent }) {
    const buckets = [5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5]
    const counts = buckets.map(r => reviews.filter(rev => rev.rating === r).length)
    const max = Math.max(...counts, 1)
    const fill = accent
        ? `rgba(${accent.r},${accent.g},${accent.b},0.75)`
        : '#5a5652'

    return (
        <div className='rating-dist'>
            {buckets.map((rating, i) => (
                <div key={rating} className='rating-dist__row'>
                    <span className='rating-dist__label'>
                        {Number.isInteger(rating) ? rating : ''}
                    </span>
                    <div className='rating-dist__track'>
                        <div
                            className='rating-dist__bar'
                            style={{
                                width: counts[i] > 0 ? `${(counts[i] / max) * 100}%` : '0%',
                                background: fill,
                            }}
                        />
                    </div>
                    <span className='rating-dist__count'>
                        {counts[i] > 0 ? counts[i] : ''}
                    </span>
                </div>
            ))}
        </div>
    )
}

// ── Main component ───────────────────────────────────────────────────────────
function AlbumDetails() {
    const { mbid } = useParams()
    const { state } = useLocation()
    const fromArtist = state?.fromArtist
    const { user } = useAuth()

    const [album, setAlbum] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [imgError, setImgError] = useState(false)
    const [lightboxOpen, setLightboxOpen] = useState(false)

    const [reviews, setReviews] = useState([])
    const [reviewsLoading, setReviewsLoading] = useState(true)
    const [showModal, setShowModal] = useState(false)

    const fetchAlbum = useCallback(() => {
        return api(`/albums/${mbid}`)
            .then(data => setAlbum(data))
            .catch(err => setError(err.message || 'Error fetching album'))
    }, [mbid])

    const fetchReviews = useCallback(() => {
        setReviewsLoading(true)
        api(`/albums/${mbid}/reviews`)
            .then(data => setReviews(data.reviews || []))
            .catch(() => setReviews([]))
            .finally(() => setReviewsLoading(false))
    }, [mbid])

    useEffect(() => {
        window.scrollTo(0, 0)
        setLoading(true)
        setError(null)
        setAlbum(null)
        setImgError(false)

        fetchAlbum().finally(() => setLoading(false))
        fetchReviews()
    }, [mbid])

    const handleReviewSubmitted = () => {
        fetchReviews()
        fetchAlbum()
    }

    if (loading) return <AlbumDetailSkeleton />
    if (error) return <div className='album-detail-error'>Error: {error}</div>
    if (!album) return null

    const hasReviewed = reviews.some(r => r.username === user?.username)
    const multiDisc = album.tracklist && album.tracklist.length > 1
    const trackCount = album.tracklist
        ? album.tracklist.reduce((sum, disc) => sum + disc.tracks.length, 0)
        : 0

    const accent = parseHex(album.color_accent)
    const accentBg = accent
        ? `radial-gradient(ellipse 100% 55% at 50% 0%, rgba(${accent.r},${accent.g},${accent.b},0.5) 0%, transparent 100%)`
        : undefined

    return (
        <div className='album-detail-root'>
            {accentBg && <div className='album-accent-glow' style={{ background: accentBg }} />}

            {/* ── Hero ── */}
            <div className='album-detail-hero'>
                <div className='album-detail-hero__cover-wrap'>
                    {album.cover_url && !imgError ? (
                        <img
                            className='album-detail-hero__cover'
                            src={album.cover_url}
                            alt={`${album.title} cover`}
                            onError={() => setImgError(true)}
                            onClick={() => setLightboxOpen(true)}
                            title='Click to enlarge'
                        />
                    ) : (
                        <div className='album-detail-hero__cover-fallback'>
                            <img src='/album-fallback.svg' alt='Album' className='album-card__fallback-svg' />
                        </div>
                    )}
                </div>

                <div className='album-detail-hero__info'>
                    {fromArtist && (
                        <Link
                            to={`/artists/${fromArtist.mbid}`}
                            className='album-detail-back'
                        >
                            ← {fromArtist.name}
                        </Link>
                    )}
                    <p className='album-detail-hero__label'>Album</p>
                    <h1 className='album-detail-hero__title'>{album.title}</h1>

                    <p className='album-detail-hero__artists'>
                        {album.artists.map((artist, i) => (
                            <span key={artist.mbid}>
                                <Link to={`/artists/${artist.mbid}`}>{artist.name}</Link>
                                {i < album.artists.length - 1 && ', '}
                            </span>
                        ))}
                    </p>

                    <p className='album-detail-hero__year'>{album.release_year}</p>

                    <div className='album-detail-hero__meta'>
                        {album.average_rating !== null && album.average_rating !== undefined ? (
                            <>
                                <div className='album-detail-rating'>
                                    <StarRating rating={album.average_rating} />
                                    <span className='album-detail-rating__value'>
                                        {album.average_rating.toFixed(1)}
                                    </span>
                                    <span className='album-detail-rating__count'>
                                        {album.review_count} {album.review_count === 1 ? 'review' : 'reviews'}
                                    </span>
                                </div>
                                {reviews.length > 0 && (
                                    <RatingDistribution reviews={reviews} accent={accent} />
                                )}
                            </>
                        ) : (
                            <p className='album-detail-rating--none'>No reviews yet</p>
                        )}

                        {trackCount > 0 && (
                            <p className='album-detail-hero__track-count'>
                                {trackCount} tracks
                                {multiDisc && ` · ${album.tracklist.length} discs`}
                            </p>
                        )}
                    </div>

                    {!hasReviewed && (
                        <button
                            className='album-detail-review-btn'
                            onClick={() => setShowModal(true)}
                        >
                            + Write a Review
                        </button>
                    )}
                </div>
            </div>

            {/* ── Tracklist ── */}
            <div className='album-detail-divider'>
                <span className='album-detail-divider__line' />
                <span className='album-detail-divider__label'>Tracklist</span>
                <span className='album-detail-divider__line' />
            </div>

            {!album.tracklist || album.tracklist.length === 0 ? (
                <div className='album-detail-empty'>
                    <p className='album-detail-empty__title'>No tracklist available</p>
                    <p className='album-detail-empty__sub'>
                        Track data for this album hasn't been seeded yet.
                    </p>
                </div>
            ) : (
                <div className='album-detail-tracklist'>
                    {album.tracklist.map(disc => (
                        <div key={disc.disc_number} className='album-detail-disc'>
                            {multiDisc && (
                                <p className='album-detail-disc__label'>Disc {disc.disc_number}</p>
                            )}
                            <table className='album-detail-tracks'>
                                <tbody>
                                    {disc.tracks.map(track => (
                                        <TrackRow key={track.track_number} track={track} albumArtists={album.artists} />
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ))}
                </div>
            )}

            {/* ── Reviews ── */}
            <div className='album-detail-divider' style={{ marginTop: '3.5rem' }}>
                <span className='album-detail-divider__line' />
                <span className='album-detail-divider__label'>Reviews</span>
                <span className='album-detail-divider__line' />
            </div>

            <ReviewList
                reviews={reviews}
                loading={reviewsLoading}
                onUpdated={handleReviewSubmitted}
                onDeleted={handleReviewSubmitted}
            />

            {/* ── Modals ── */}
            {showModal && (
                <ReviewModal
                    mbid={mbid}
                    albumTitle={album.title}
                    onClose={() => setShowModal(false)}
                    onSubmitted={handleReviewSubmitted}
                />
            )}

            {lightboxOpen && album.cover_url && !imgError && (
                <CoverLightbox
                    src={album.cover_url}
                    alt={`${album.title} cover`}
                    onClose={() => setLightboxOpen(false)}
                />
            )}
        </div>
    )
}

export default AlbumDetails;