import React from 'react';
import './Skeleton.css';

// Generic shimmer block
export function Skeleton({ width, height, radius, className = '' }) {
    return (
        <div
            className={`skeleton ${className}`}
            style={{
                width: width || '100%',
                height: height || '1rem',
                borderRadius: radius || '4px',
            }}
        />
    );
}

// Album card skeleton — matches the AlbumCard proportions
export function AlbumCardSkeleton() {
    return (
        <div className='album-card-skeleton'>
            <div className='album-card-skeleton__img skeleton' />
        </div>
    );
}

// Album detail hero skeleton
export function AlbumDetailSkeleton() {
    return (
        <div className='album-detail-skeleton'>
            <div className='album-detail-skeleton__hero'>
                <div className='album-detail-skeleton__cover skeleton' />
                <div className='album-detail-skeleton__info'>
                    <Skeleton width='60px' height='0.7rem' />
                    <Skeleton width='75%' height='2.2rem' radius='6px' className='mt-sm' />
                    <Skeleton width='40%' height='0.9rem' className='mt-sm' />
                    <Skeleton width='30px' height='0.8rem' className='mt-sm' />
                    <Skeleton width='160px' height='1rem' className='mt-md' />
                    <Skeleton width='130px' height='2.4rem' radius='4px' className='mt-md' />
                </div>
            </div>
            <div className='album-detail-skeleton__tracks'>
                {[...Array(8)].map((_, i) => (
                    <div key={i} className='album-detail-skeleton__track-row'>
                        <Skeleton width='24px' height='0.8rem' />
                        <Skeleton width={`${55 + Math.random() * 30}%`} height='0.8rem' />
                        <Skeleton width='36px' height='0.8rem' />
                    </div>
                ))}
            </div>
        </div>
    );
}

// Artist list card skeleton — circular to match ArtistCard
export function ArtistCardSkeleton() {
    return (
        <div className='artist-card-skeleton'>
            <div className='artist-card-skeleton__img skeleton' />
            <div className='artist-card-skeleton__name skeleton' />
        </div>
    )
}

// Artist detail hero skeleton
export function ArtistDetailSkeleton() {
    return (
        <div className='artist-detail-skeleton'>
            <div className='artist-detail-skeleton__hero'>
                <div className='artist-detail-skeleton__photo skeleton' />
                <div className='artist-detail-skeleton__info'>
                    <Skeleton width='50px' height='0.7rem' />
                    <Skeleton width='55%' height='2.4rem' radius='6px' className='mt-sm' />
                    <Skeleton width='80px' height='0.8rem' className='mt-sm' />
                </div>
            </div>
            <div className='artist-detail-skeleton__grid'>
                {[...Array(6)].map((_, i) => (
                    <div key={i} className='album-card-skeleton'>
                        <div className='album-card-skeleton__img skeleton' />
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Skeleton;