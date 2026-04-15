import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext.jsx';
import api from '@/api/client.js';
import './Home.css';

function Home() {
    const { isAuthenticated } = useAuth()
    const [latestReviews, setLatestReviews] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api('/')
            .then(data => setLatestReviews(data.latest_reviews || []))
            .catch(() => setLatestReviews([]))
            .finally(() => setLoading(false))
    }, [])

    return (
        <div className='home-root'>
            <section className='home-hero'>
                <h1 className='home-hero__title'>
                    Your music.<br />Your story.
                </h1>
                <p className='home-hero__sub'>
                    Discover albums, share reviews, and connect with listeners who care about music as much as you do.
                </p>
                {!isAuthenticated && (
                    <div className='home-hero__actions'>
                        <Link to='/albums' className='home-hero__cta'>
                            Browse Albums
                        </Link>
                    </div>
                )}
            </section>

            {latestReviews.length > 0 && (
                <section className='home-recent'>
                    <div className='home-recent__header'>
                        <span className='home-recent__line' />
                        <span className='home-recent__label'>Recent Reviews</span>
                        <span className='home-recent__line' />
                    </div>
                    <div className='home-recent__grid'>
                        {latestReviews.map((review, i) => (
                            <div key={i} className='home-review-card'>
                                <div className='home-review-card__top'>
                                    <span className='home-review-card__album'>{review.album}</span>
                                    {review.artist && (
                                        <span className='home-review-card__artist'>{review.artist}</span>
                                    )}
                                </div>
                                <div className='home-review-card__bottom'>
                                    <span className='home-review-card__stars'>
                                        {'★'.repeat(Math.floor(review.rating))}
                                        {review.rating % 1 >= 0.5 ? '½' : ''}
                                    </span>
                                    <span className='home-review-card__user'>by {review.username}</span>
                                </div>
                                {review.comment && (
                                    <p className='home-review-card__comment'>{review.comment}</p>
                                )}
                            </div>
                        ))}
                    </div>
                </section>
            )}
        </div>
    )
}

export default Home
