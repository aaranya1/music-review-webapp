import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '@/api/client.js';
import AlbumCard from '@/features/albums/components/AlbumCard.jsx';
import { ArtistDetailSkeleton } from '@/components/ui/Skeleton.jsx';
import { getAvatarColor, parseHex } from '@/utils/avatar.js';
import './ArtistDetails.css';

function ArtistDetails() {
    const { mbid } = useParams()

    const [artist, setArtist] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [sortDir, setSortDir] = useState('desc')

    useEffect(() => {
        window.scrollTo(0, 0)
        setLoading(true)
        setError(null)
        setArtist(null)

        api(`/artists/${mbid}`)
            .then(data => setArtist(data))
            .catch(err => setError(err.message || 'Error fetching artist'))
            .finally(() => setLoading(false))
    }, [mbid])

    if (loading) return <ArtistDetailSkeleton />
    if (error) return <div className='artist-error'>Error: {error}</div>
    if (!artist) return null

    const albums      = artist.albums || []
    const initial     = artist.name.charAt(0).toUpperCase()
    const avatarColor = getAvatarColor(artist.name)

    const accent = parseHex(artist.color_accent)
    const cinematicGlowBg = accent
        ? `radial-gradient(ellipse 90% 80% at 15% 100%, rgba(${accent.r},${accent.g},${accent.b},0.4) 0%, transparent 65%)`
        : undefined
    const compactGlowBg = accent
        ? `radial-gradient(ellipse 100% 60% at 0% 0%, rgba(${accent.r},${accent.g},${accent.b},0.4) 0%, transparent 75%)`
        : undefined

    const discography = albums
        .slice()
        .sort((a, b) => sortDir === 'desc'
            ? (b.release_year || 0) - (a.release_year || 0)
            : (a.release_year || 0) - (b.release_year || 0)
        )

    const sortControl = albums.length > 1 ? (
        <div className='artist-sort'>
            <button
                className={`artist-sort__btn${sortDir === 'desc' ? ' artist-sort__btn--active' : ''}`}
                onClick={() => setSortDir('desc')}
            >Newest</button>
            <button
                className={`artist-sort__btn${sortDir === 'asc' ? ' artist-sort__btn--active' : ''}`}
                onClick={() => setSortDir('asc')}
            >Oldest</button>
        </div>
    ) : null

    const albumGrid = discography.length === 0 ? (
        <div className='artist-empty'>
            <p className='artist-empty__title'>No releases found</p>
            <p className='artist-empty__sub'>
                This artist's discography hasn't been seeded yet.
            </p>
        </div>
    ) : (
        <div className='artist-album-grid'>
            {discography.map((album, i) => (
                <div
                    key={album.mbid}
                    className='artist-album-entry'
                    style={{ animationDelay: `${i * 35}ms` }}
                >
                    <AlbumCard album={album} fromArtist={{ mbid: artist.mbid, name: artist.name }} />
                </div>
            ))}
        </div>
    )

    return (
        <div className='artist-detail-root'>

            {artist.background_url ? (
                <>
                    {/* Background image — position: absolute so it scrolls with the page */}
                    <div
                        className='artist-hero-bg'
                        style={{ backgroundImage: `url(${artist.background_url})` }}
                    />
                    <div className='artist-hero-overlay' />
                    {cinematicGlowBg && <div className='artist-accent-glow' style={{ background: cinematicGlowBg }} />}

                    {/* Transparent spacer — creates scrollable space above the panel */}
                    <div className='artist-hero-space' />

                    {/* Sticky panel — sibling of spacer so it stays locked for the full page */}
                    <div className='artist-panel'>
                        {artist.image_url ? (
                            <img
                                className='artist-panel__photo'
                                src={artist.image_url}
                                alt={artist.name}
                            />
                        ) : (
                            <div
                                className='artist-panel__fallback'
                                style={{ borderColor: avatarColor, color: avatarColor }}
                            >
                                {initial}
                            </div>
                        )}
                        <div className='artist-panel__info'>
                            <p className='artist-hero__label'>Artist</p>
                            <h1 className='artist-panel__name'>{artist.name}</h1>
                            <p className='artist-hero__count'>
                                {albums.length} {albums.length === 1 ? 'release' : 'releases'}
                            </p>
                        </div>
                    </div>

                    {/* Discography — solid dark background, scrolls below the hero */}
                    <div className='artist-content'>
                        <div className='artist-discography-header'>
                            <div className='artist-divider'>
                                <span className='artist-divider__line' />
                                <span className='artist-divider__label'>Discography</span>
                                <span className='artist-divider__line' />
                            </div>
                            {sortControl}
                        </div>
                        {albumGrid}
                    </div>
                </>
            ) : (
                <>
                    {compactGlowBg && <div className='artist-compact-glow' style={{ background: compactGlowBg }} />}
                    {/* Compact header for artists without a background image */}
                    <div className='artist-compact-header'>
                        <div className='artist-compact-header__photo-wrap'>
                            {artist.image_url ? (
                                <img
                                    className='artist-compact-header__photo'
                                    src={artist.image_url}
                                    alt={artist.name}
                                />
                            ) : (
                                <div
                                    className='artist-compact-header__photo-fallback'
                                    style={{ borderColor: avatarColor, color: avatarColor }}
                                >
                                    {initial}
                                </div>
                            )}
                        </div>
                        <div className='artist-compact-header__info'>
                            <p className='artist-hero__label'>Artist</p>
                            <h1 className='artist-hero__name'>{artist.name}</h1>
                            <p className='artist-hero__count'>
                                {albums.length} {albums.length === 1 ? 'release' : 'releases'}
                            </p>
                        </div>
                    </div>

                    <div className='artist-detail-content'>
                        <div className='artist-discography-header'>
                            <div className='artist-divider'>
                                <span className='artist-divider__line' />
                                <span className='artist-divider__label'>Discography</span>
                                <span className='artist-divider__line' />
                            </div>
                            {sortControl}
                        </div>
                        {albumGrid}
                    </div>
                </>
            )}
        </div>
    )
}

export default ArtistDetails;
