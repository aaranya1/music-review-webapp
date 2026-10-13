import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useApi } from '@/utils/useApi.js';
import { useScrollRestoration } from '@/utils/useScrollRestoration.js';
import { getAvatarColor } from '@/utils/avatar.js';
import { ArtistCardSkeleton } from '@/components/ui/Skeleton.jsx';
import './ArtistList.css';

function ArtistCard({ artist }) {
    const initial     = artist.name.charAt(0).toUpperCase()
    const avatarColor = getAvatarColor(artist.name)

    return (
        <Link to={`/artists/${artist.mbid}`} className='artist-card'>
            <div className='artist-card__img-wrap'>
                {artist.image_url ? (
                    <img
                        src={artist.image_url}
                        alt={artist.name}
                        loading='lazy'
                        className='artist-card__img'
                        onError={e => { e.currentTarget.style.display = 'none' }}
                    />
                ) : (
                    <div
                        className='artist-card__fallback'
                        style={{ borderColor: avatarColor, color: avatarColor }}
                    >
                        {initial}
                    </div>
                )}
            </div>
            <p className='artist-card__name'>{artist.name}</p>
        </Link>
    )
}

function ArtistList() {
    useScrollRestoration()
    const [searchParams, setSearchParams] = useSearchParams()
    const [page, setPage] = useState(() => {
        const p = Number(searchParams.get('page'))
        return p > 0 ? p : 1
    })

    const { data, error, loading, reload } = useApi(`/artists?page=${page}&per_page=20`)
    const artists    = data?.artists || []
    const totalPages = data?.total_pages || 1

    const handleSetPage = (newPage) => {
        setPage(newPage)
        setSearchParams({ page: String(newPage) }, { replace: true })
    }

    return (
        <div className='artist-list-root'>

            <div className='artist-list-header'>
                <h2 className='artist-list-header__title'>Artists</h2>
                {!loading && !error && (
                    <span className='artist-list-header__page'>
                        Page {page} of {totalPages}
                    </span>
                )}
            </div>

            {error && (
                <div className='artist-list-error'>
                    <p>Something went wrong.</p>
                    <button onClick={reload}>Retry</button>
                </div>
            )}

            <div className='artist-grid'>
                {loading
                    ? [...Array(20)].map((_, i) => <ArtistCardSkeleton key={i} />)
                    : artists.map(artist => (
                        <ArtistCard key={artist.mbid} artist={artist} />
                    ))
                }
            </div>

            {!loading && !error && artists.length === 0 && (
                <div className='artist-list-empty'>
                    <p className='artist-list-empty__title'>No artists yet</p>
                    <p className='artist-list-empty__sub'>
                        The catalogue is still being seeded. Check back soon.
                    </p>
                </div>
            )}

            {!loading && !error && artists.length > 0 && (
                <div className='pagination'>
                    <button
                        onClick={() => handleSetPage(page - 1)}
                        disabled={page === 1}
                    >
                        ← Prev
                    </button>
                    <span className='page-label'>{page} / {totalPages}</span>
                    <button
                        onClick={() => handleSetPage(page + 1)}
                        disabled={page === totalPages}
                    >
                        Next →
                    </button>
                </div>
            )}
        </div>
    )
}

export default ArtistList;
