import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '@/api/client.js';
import { useScrollRestoration } from '@/utils/useScrollRestoration.js';
import AlbumCard from './AlbumCard.jsx';
import { AlbumCardSkeleton } from '@/components/ui/Skeleton.jsx';
import './AlbumList.css';

function AlbumList() {
    useScrollRestoration()
    const [searchParams, setSearchParams] = useSearchParams()
    const [albums, setAlbums]       = useState([])
    const [loading, setLoading]     = useState(true)
    const [error, setError]         = useState(null)
    const [totalPages, setTotalPages] = useState(1)
    const [page, setPage] = useState(() => {
        const p = Number(searchParams.get('page'))
        return p > 0 ? p : 1
    })

    useEffect(() => {
        setLoading(true)
        setError(null)

        api(`/albums?page=${page}&per_page=20`)
            .then(data => {
                setAlbums(data.albums || [])
                setTotalPages(data.total_pages || 1)
            })
            .catch(err => setError(err.message || 'Error fetching albums'))
            .finally(() => setLoading(false))
    }, [page])

    return (
        <div className='album-list-root'>

            <div className='album-list-header'>
                <h2 className='album-list-header__title'>Albums</h2>
                {!loading && !error && (
                    <span className='album-list-header__page'>
                        Page {page} of {totalPages}
                    </span>
                )}
            </div>

            {error && (
                <div className='album-list-error'>
                    <p>Something went wrong.</p>
                    <button onClick={() => setPage(p => p)}>Retry</button>
                </div>
            )}

            {/* ── Grid — skeletons while loading, cards when done ── */}
            <div className='album-grid'>
                {loading
                    ? [...Array(20)].map((_, i) => <AlbumCardSkeleton key={i} />)
                    : albums.length === 0
                        ? null
                        : albums.map(album => (
                            <AlbumCard key={album.mbid} album={album} />
                        ))
                }
            </div>

            {/* ── Empty state ── */}
            {!loading && !error && albums.length === 0 && (
                <div className='album-list-empty'>
                    <p className='album-list-empty__title'>No albums yet</p>
                    <p className='album-list-empty__sub'>
                        The catalogue is still being seeded. Check back soon.
                    </p>
                </div>
            )}

            {/* ── Pagination ── */}
            {!loading && !error && albums.length > 0 && (
                <div className='pagination'>
                    <button
                        onClick={() => { const p = page - 1; setPage(p); setSearchParams({ page: String(p) }, { replace: true }) }}
                        disabled={page === 1}
                    >
                        ← Prev
                    </button>
                    <span className='page-label'>{page} / {totalPages}</span>
                    <button
                        onClick={() => { const p = page + 1; setPage(p); setSearchParams({ page: String(p) }, { replace: true }) }}
                        disabled={page === totalPages}
                    >
                        Next →
                    </button>
                </div>
            )}
        </div>
    )
}

export default AlbumList;