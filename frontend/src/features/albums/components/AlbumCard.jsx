import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './AlbumCard.css';

function AlbumCard({ album, fromArtist }) {
    const [imgError, setImgError] = useState(false)
    const navigate = useNavigate()

    return (
        <Link to={`/albums/${album.mbid}`} state={fromArtist ? { fromArtist } : undefined} className='album-card'>
            <div className='album-card__img-wrap'>
                {album.cover_url && !imgError ? (
                    <img
                        src={album.cover_url}
                        alt={`${album.title} cover`}
                        loading='lazy'
                        className='album-card__img'
                        onError={() => setImgError(true)}
                    />
                ) : (
                    <div className='album-card__fallback'>
                        <img src='/album-fallback.svg' alt='Album' className='album-card__fallback-svg' />
                    </div>
                )}

                <div className='album-card__overlay'>
                    <p className='album-card__overlay-artists'>
                        {album.artists?.map((artist, i) => (
                            <span key={artist.mbid}>
                                <span
                                    className='album-card__overlay-artist-link'
                                    onClick={e => {
                                        e.preventDefault()
                                        navigate(`/artists/${artist.mbid}`)
                                    }}
                                >
                                    {artist.name}
                                </span>
                                {i < album.artists.length - 1 && ', '}
                            </span>
                        ))}
                    </p>
                    <h3 className='album-card__overlay-title'>{album.title}</h3>
                    <span className='album-card__overlay-year'>{album.release_year}</span>
                </div>
            </div>
        </Link>
    );
}

export default AlbumCard;