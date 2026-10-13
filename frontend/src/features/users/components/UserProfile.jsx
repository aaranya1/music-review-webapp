import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ClipLoader } from 'react-spinners';
import { useAuth } from '@/context/useAuth.js';
import { useApi } from '@/utils/useApi.js';
import { getAvatarColor } from '@/utils/avatar.js';
import api from '@/api/client.js';
import StarRating from '@/components/ui/StarRating.jsx';
import AlbumCard from '@/features/albums/components/AlbumCard.jsx';
import ListCard from '@/features/lists/components/ListCard.jsx';
import './UserProfile.css';

function Loader() {
    return (
        <div className='profile-reviews-loader'>
            <ClipLoader color='#c8a96e' loading size={36} />
        </div>
    )
}

function Pagination({ page, totalPages, setPage }) {
    if (totalPages <= 1) return null
    return (
        <div className='profile-pagination'>
            <button onClick={() => setPage(p => p - 1)} disabled={page === 1}>← Prev</button>
            <span className='profile-pagination__label'>{page} / {totalPages}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>Next →</button>
        </div>
    )
}

function ReviewsTab({ userId, isOwnProfile, username }) {
    const [page, setPage] = useState(1)
    const { data, loading } = useApi(`/users/${userId}/reviews?page=${page}&per_page=20`)
    const reviews = data?.reviews || []

    if (loading) return <Loader />
    if (reviews.length === 0) {
        return (
            <p className='profile-empty'>
                {isOwnProfile ? "You haven't reviewed any albums yet." : `${username} hasn't reviewed any albums yet.`}
            </p>
        )
    }

    return (
        <>
            <div className='profile-review-list'>
                {reviews.map((review, i) => (
                    <Link
                        key={review.id}
                        to={`/albums/${review.album.mbid}`}
                        className='profile-review-card'
                        style={{ animationDelay: `${i * 35}ms` }}
                    >
                        <div className='profile-review-card__cover-wrap'>
                            {review.album.cover_url ? (
                                <img
                                    src={review.album.cover_url}
                                    alt={review.album.title}
                                    className='profile-review-card__cover'
                                    onError={(e) => { e.target.src = '/fallback.jpg' }}
                                />
                            ) : (
                                <div className='profile-review-card__cover-fallback'>
                                    {review.album.title?.charAt(0)}
                                </div>
                            )}
                        </div>

                        <div className='profile-review-card__body'>
                            <h3 className='profile-review-card__title'>{review.album.title}</h3>
                            <div className='profile-review-card__rating'>
                                <StarRating rating={review.rating} className='profile-star-rating' />
                                <span className='profile-review-card__rating-val'>{review.rating.toFixed(1)}</span>
                                {review.updated_at && <span className='profile-review-card__edited'>edited</span>}
                            </div>
                            {review.review_text && (
                                <p className='profile-review-card__comment'>{review.review_text}</p>
                            )}
                        </div>
                    </Link>
                ))}
            </div>
            <Pagination page={page} totalPages={data?.total_pages || 1} setPage={setPage} />
        </>
    )
}

function ListsTab({ userId, isOwnProfile, username }) {
    const [page, setPage] = useState(1)
    const { data, loading } = useApi(`/users/${userId}/lists?page=${page}&per_page=24`)
    const lists = data?.lists || []

    if (loading) return <Loader />
    if (lists.length === 0) {
        return (
            <p className='profile-empty'>
                {isOwnProfile ? <>No lists yet. <Link to='/lists'>Make one</Link>.</> : `${username} has no public lists.`}
            </p>
        )
    }
    return (
        <>
            <div className='list-grid'>{lists.map(l => <ListCard key={l.id} list={l} />)}</div>
            <Pagination page={page} totalPages={data?.total_pages || 1} setPage={setPage} />
        </>
    )
}

function FollowTab({ userId, kind, username }) {
    const [page, setPage] = useState(1)
    const { data, loading } = useApi(`/users/${userId}/${kind}?page=${page}&per_page=50`)
    const people = data?.[kind] || []

    if (loading) return <Loader />
    if (people.length === 0) {
        return (
            <p className='profile-empty'>
                {kind === 'followers' ? `No one follows ${username} yet.` : `${username} isn't following anyone yet.`}
            </p>
        )
    }
    return (
        <>
            <ul className='profile-people'>
                {people.map(p => {
                    const color = getAvatarColor(p.username)
                    return (
                        <li key={p.id}>
                            <Link to={`/users/${p.id}`} className='profile-person'>
                                <span className='profile-person__avatar' style={{ borderColor: color, color }}>
                                    {p.username.charAt(0).toUpperCase()}
                                </span>
                                {p.username}
                            </Link>
                        </li>
                    )
                })}
            </ul>
            <Pagination page={page} totalPages={data?.total_pages || 1} setPage={setPage} />
        </>
    )
}

function WantToListenTab() {
    const [page, setPage] = useState(1)
    const { data, loading } = useApi(`/backlog?page=${page}&per_page=20`)
    const entries = data?.backlog || []

    if (loading) return <Loader />
    if (entries.length === 0) {
        return <p className='profile-empty'>Nothing here yet. Use "+ Want to Listen" on any album page.</p>
    }
    return (
        <>
            <div className='album-grid'>{entries.map(e => <AlbumCard key={e.id} album={e.album} />)}</div>
            <Pagination page={page} totalPages={data?.total_pages || 1} setPage={setPage} />
        </>
    )
}

function FollowButton({ userId, following, onChange }) {
    const { isAuthenticated, openLogin } = useAuth()
    const [busy, setBusy] = useState(false)

    const toggle = async () => {
        if (!isAuthenticated) return openLogin()
        setBusy(true)
        try {
            await api(`/users/${userId}/follow`, { method: following ? 'DELETE' : 'POST' })
            onChange(!following)
        } catch {
            window.alert('Could not update follow. Please try again.')
        } finally {
            setBusy(false)
        }
    }

    return (
        <button
            type='button'
            className={`profile-follow-btn ${following ? 'profile-follow-btn--on' : ''}`}
            onClick={toggle}
            disabled={busy}
        >
            {following ? 'Following' : 'Follow'}
        </button>
    )
}

function UserProfile() {
    const { user_id } = useParams()
    const { user: currentUser } = useAuth()
    const profileReq = useApi(`/users/${user_id}`)
    const profile = profileReq.data

    // Tab and follow state are tied to the user being viewed, so they reset on navigation
    const [tabState, setTabState] = useState({ userId: user_id, tab: 'reviews' })
    const tab = tabState.userId === user_id ? tabState.tab : 'reviews'
    const setTab = (t) => setTabState({ userId: user_id, tab: t })

    const [followState, setFollowState] = useState({ userId: null, following: null })
    const followOverride = followState.userId === user_id ? followState.following : null

    const isOwnProfile = currentUser?.id === parseInt(user_id)

    if (profileReq.loading && !profile) {
        return (
            <div className='profile-loader'>
                <ClipLoader color='#c8a96e' loading size={60} aria-label='Loading' />
            </div>
        )
    }

    if (profileReq.error) return <div className='profile-error'>This user doesn't exist.</div>
    if (!profile) return null

    const following = followOverride ?? !!profile.is_following
    // Adjust the follower count for a follow/unfollow made on this page
    const followerCount = profile.follower_count +
        (followOverride === null ? 0 : (followOverride ? 1 : 0) - (profile.is_following ? 1 : 0))

    const initial = profile.username.charAt(0).toUpperCase()
    const avatarColor = getAvatarColor(profile.username)

    const tabs = [
        ['reviews', 'Reviews'],
        ['lists', 'Lists'],
        ['followers', 'Followers'],
        ['following', 'Following'],
        ...(isOwnProfile ? [['want', 'Want to Listen']] : []),
    ]

    return (
        <div className='profile-root'>

            {/* ── Header ── */}
            <div className='profile-header'>
                <div className='profile-avatar' style={{ borderColor: avatarColor, color: avatarColor }}>{initial}</div>
                <div className='profile-header__info'>
                    <p className='profile-header__label'>
                        {isOwnProfile ? 'Your Profile' : 'Member'}
                    </p>
                    <h1 className='profile-header__username'>{profile.username}</h1>
                    <p className='profile-header__stats'>
                        <button className='profile-header__stat' onClick={() => setTab('reviews')}>
                            <span className='profile-header__stat-value'>{profile.review_count}</span>
                            {' '}{profile.review_count === 1 ? 'review' : 'reviews'}
                        </button>
                        <button className='profile-header__stat' onClick={() => setTab('followers')}>
                            <span className='profile-header__stat-value'>{followerCount}</span>
                            {' '}{followerCount === 1 ? 'follower' : 'followers'}
                        </button>
                        <button className='profile-header__stat' onClick={() => setTab('following')}>
                            <span className='profile-header__stat-value'>{profile.following_count}</span> following
                        </button>
                    </p>
                </div>
                {!isOwnProfile && (
                    <FollowButton
                        userId={profile.id}
                        following={following}
                        onChange={(value) => setFollowState({ userId: user_id, following: value })}
                    />
                )}
            </div>

            {/* ── Tabs ── */}
            <div className='feed__tabs profile-tabs' role='tablist'>
                {tabs.map(([key, label]) => (
                    <button
                        key={key}
                        role='tab'
                        aria-selected={tab === key}
                        className={`feed__tab ${tab === key ? 'feed__tab--active' : ''}`}
                        onClick={() => setTab(key)}
                    >
                        {label}
                    </button>
                ))}
            </div>

            {/* key={user_id} so each tab's paging resets when switching users */}
            <div key={user_id}>
                {tab === 'reviews' && <ReviewsTab userId={user_id} isOwnProfile={isOwnProfile} username={profile.username} />}
                {tab === 'lists' && <ListsTab userId={user_id} isOwnProfile={isOwnProfile} username={profile.username} />}
                {tab === 'followers' && <FollowTab userId={user_id} kind='followers' username={profile.username} />}
                {tab === 'following' && <FollowTab userId={user_id} kind='following' username={profile.username} />}
                {tab === 'want' && isOwnProfile && <WantToListenTab />}
            </div>
        </div>
    )
}

export default UserProfile
