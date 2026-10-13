import React, { useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { useApi } from '@/utils/useApi.js';
import ReviewCard from './ReviewCard.jsx';
import './Feed.css';

const TABS = [
    { key: 'following', label: 'Following', path: '/feed' },
    { key: 'popular', label: 'Popular', path: '/feed/popular' },
]

/** One page of the feed. Each page fetches itself, so "Load more" just adds a page. */
function FeedPage({ path, page, isLast, onMore, onEmpty }) {
    const { data, error, loading, reload } = useApi(`${path}?page=${page}&per_page=20`)

    if (loading && !data) {
        return <div className='feed__loader'><ClipLoader color='#c8a96e' size={28} aria-label='Loading' /></div>
    }
    if (error) {
        return (
            <div className='feed__status'>
                Couldn't load the feed. <button className='feed__link' onClick={reload}>Retry</button>
            </div>
        )
    }

    const reviews = data?.reviews || []
    if (page === 1 && reviews.length === 0) return onEmpty

    return (
        <>
            {reviews.map(r => <ReviewCard key={r.id} review={r} />)}
            {isLast && data.page < data.total_pages && (
                <button className='feed__more' onClick={onMore}>Load more</button>
            )}
        </>
    )
}

function Feed() {
    const [tab, setTab] = useState('following')
    // Page count is tied to the tab, so switching tabs starts from page 1
    const [pages, setPages] = useState({ tab: 'following', count: 1 })
    const count = pages.tab === tab ? pages.count : 1
    const current = TABS.find(t => t.key === tab)

    const empty = tab === 'following' ? (
        <div className='feed__status'>
            No reviews from people you follow yet.{' '}
            <button className='feed__link' onClick={() => setTab('popular')}>See popular reviews</button>
        </div>
    ) : (
        <div className='feed__status'>No reviews yet.</div>
    )

    return (
        <div className='feed'>
            <div className='feed__tabs' role='tablist'>
                {TABS.map(t => (
                    <button
                        key={t.key}
                        role='tab'
                        aria-selected={tab === t.key}
                        className={`feed__tab ${tab === t.key ? 'feed__tab--active' : ''}`}
                        onClick={() => setTab(t.key)}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            <div className='feed__list'>
                {Array.from({ length: count }, (_, i) => (
                    <FeedPage
                        key={`${tab}-${i + 1}`}
                        path={current.path}
                        page={i + 1}
                        isLast={i + 1 === count}
                        onMore={() => setPages({ tab, count: count + 1 })}
                        onEmpty={empty}
                    />
                ))}
            </div>
        </div>
    )
}

export default Feed
