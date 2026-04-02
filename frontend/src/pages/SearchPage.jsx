import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../api/client.js';
import './SearchPage.css';

function AlbumResult({ album }) {
    return (
        <Link to={`/albums/${album.mbid}`} className='search-result-card'>
            <div className='search-result-card__cover-wrap'>
                {album.cover_url ? (
                    <img
                        src={album.cover_url}
                        alt={album.title}
                        className='search-result-card__cover'
                        onError={e => { e.target.src = '/fallback.jpg'; }}
                    />
                ) : (
                    <div className='search-result-card__cover-fallback'>
                        {album.title?.charAt(0)}
                    </div>
                )}
            </div>
            <div className='search-result-card__body'>
                <h3 className='search-result-card__title'>{album.title}</h3>
                <p className='search-result-card__sub'>
                    {album.artists?.map(a => a.name).join(', ')}
                    {album.release_year && (
                        <span className='search-result-card__year'> · {album.release_year}</span>
                    )}
                </p>
            </div>
        </Link>
    );
}

function ArtistResult({ artist }) {
    const initial = artist.name?.charAt(0).toUpperCase();
    return (
        <Link to={`/artists/${artist.mbid}`} className='search-result-card'>
            <div className='search-result-card__cover-wrap search-result-card__cover-wrap--round'>
                {artist.image_url ? (
                    <img
                        src={artist.image_url}
                        alt={artist.name}
                        className='search-result-card__cover'
                        onError={e => { e.target.src = '/fallback.jpg'; }}
                    />
                ) : (
                    <div className='search-result-card__cover-fallback'>
                        {initial}
                    </div>
                )}
            </div>
            <div className='search-result-card__body'>
                <h3 className='search-result-card__title'>{artist.name}</h3>
                <p className='search-result-card__sub search-result-card__sub--label'>Artist</p>
            </div>
        </Link>
    );
}

function SearchPage() {
    const [searchParams, setSearchParams] = useSearchParams();
    const query = searchParams.get('q') || '';

    const [inputValue, setInputValue] = useState(query);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Sync input if query param changes externally (e.g. navbar search)
    useEffect(() => {
        setInputValue(query);
    }, [query]);

    useEffect(() => {
        if (!query.trim()) {
            setResults(null);
            return;
        }

        setLoading(true);
        setError(null);

        api(`/search?q=${encodeURIComponent(query)}`)
            .then(data => setResults(data))
            .catch(() => setError('Search failed. Please try again.'))
            .finally(() => setLoading(false));
    }, [query]);

    const handleSubmit = (e) => {
        e.preventDefault();
        const q = inputValue.trim();
        if (q) setSearchParams({ q });
    };

    const hasAlbums = results?.albums?.length > 0;
    const hasArtists = results?.artists?.length > 0;
    const isEmpty = results && !hasAlbums && !hasArtists;

    return (
        <div className='search-page'>

            {/* ── Search bar ── */}
            <form className='search-page__bar' onSubmit={handleSubmit}>
                <input
                    type='text'
                    className='search-page__input'
                    placeholder='Search albums, artists…'
                    value={inputValue}
                    onChange={e => setInputValue(e.target.value)}
                    autoFocus
                />
                <button type='submit' className='search-page__btn'>Search</button>
            </form>

            {/* ── States ── */}
            {!query && (
                <p className='search-page__hint'>Type something to search the catalogue.</p>
            )}

            {loading && (
                <div className='search-page__loading'>
                    <span className='search-page__spinner' />
                    Searching…
                </div>
            )}

            {error && <p className='search-page__error'>{error}</p>}

            {isEmpty && (
                <p className='search-page__empty'>
                    No results found for <em>"{query}"</em>.
                </p>
            )}

            {/* ── Artists section ── */}
            {hasArtists && (
                <section className='search-section'>
                    <div className='search-section__header'>
                        <span className='search-section__label'>Artists</span>
                        <span className='search-section__line' />
                    </div>
                    <div className='search-result-list'>
                        {results.artists.map((artist, i) => (
                            <div
                                key={artist.mbid}
                                style={{ animationDelay: `${i * 40}ms` }}
                                className='search-result-anim'
                            >
                                <ArtistResult artist={artist} />
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* ── Albums section ── */}
            {hasAlbums && (
                <section className='search-section'>
                    <div className='search-section__header'>
                        <span className='search-section__label'>Albums</span>
                        <span className='search-section__line' />
                    </div>
                    <div className='search-result-list'>
                        {results.albums.map((album, i) => (
                            <div
                                key={album.mbid}
                                style={{ animationDelay: `${i * 35}ms` }}
                                className='search-result-anim'
                            >
                                <AlbumResult album={album} />
                            </div>
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}

export default SearchPage;