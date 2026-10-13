import React from 'react';
import { Link } from 'react-router-dom';

/** List summary with a 2x2 cover preview (shape from _serialize_list). */
function ListCard({ list }) {
    const covers = list.preview_covers.slice(0, 4)

    return (
        <Link to={`/lists/${list.id}`} className='list-card'>
            <div className='list-card__covers'>
                {Array.from({ length: 4 }, (_, i) => (
                    covers[i]
                        ? <img key={i} src={covers[i]} alt='' loading='lazy' />
                        : <span key={i} className='list-card__cover-empty' />
                ))}
            </div>
            <div className='list-card__info'>
                <span className='list-card__title'>{list.title}</span>
                <span className='list-card__meta'>
                    {list.username} · {list.item_count} {list.item_count === 1 ? 'album' : 'albums'}
                    {!list.is_public && ' · private'}
                </span>
            </div>
        </Link>
    )
}

export default ListCard
