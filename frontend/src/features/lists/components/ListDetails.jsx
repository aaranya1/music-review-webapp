import React, { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ClipLoader } from 'react-spinners';
import { useAuth } from '@/context/useAuth.js';
import { useApi } from '@/utils/useApi.js';
import api from '@/api/client.js';
import './Lists.css';

function EditListForm({ list, onDone }) {
    const [title, setTitle] = useState(list.title)
    const [description, setDescription] = useState(list.description || '')
    const [isPublic, setIsPublic] = useState(list.is_public)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)

    const submit = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError(null)
        try {
            await api(`/lists/${list.id}`, {
                method: 'PUT',
                body: { title: title.trim(), description: description.trim() || null, is_public: isPublic },
            })
            onDone(true)
        } catch (err) {
            setError(err.message || 'Could not save changes.')
            setSaving(false)
        }
    }

    return (
        <form className='list-form' onSubmit={submit}>
            <input className='list-form__input' value={title} maxLength={255} onChange={e => setTitle(e.target.value)} />
            <textarea className='list-form__input' placeholder='Description (optional)' value={description}
                      maxLength={2000} rows={2} onChange={e => setDescription(e.target.value)} />
            <label className='list-form__check'>
                <input type='checkbox' checked={isPublic} onChange={e => setIsPublic(e.target.checked)} />
                Public
            </label>
            <div className='list-form__row'>
                {error && <span className='comment-form__error'>{error}</span>}
                <button type='button' className='list-form__cancel' onClick={() => onDone(false)}>Cancel</button>
                <button type='submit' className='comment-form__submit' disabled={!title.trim() || saving}>
                    {saving ? 'Saving…' : 'Save'}
                </button>
            </div>
        </form>
    )
}

function ListDetails() {
    const { id } = useParams()
    const navigate = useNavigate()
    const { user } = useAuth()
    const { data: list, error, loading, reload } = useApi(`/lists/${id}`)
    const [editing, setEditing] = useState(false)
    const [busy, setBusy] = useState(false)

    if (loading && !list) {
        return <div className='feed__loader'><ClipLoader color='#c8a96e' size={36} aria-label='Loading' /></div>
    }
    if (error) return <p className='feed__status'>This list doesn't exist or is private.</p>
    if (!list) return null

    const isOwner = user?.id === list.user_id
    const items = list.items || []

    // Run a mutation, then refresh the list; keeps the buttons from double-firing
    const mutate = async (fn, failMessage) => {
        setBusy(true)
        try {
            await fn()
            reload()
        } catch {
            window.alert(failMessage)
        } finally {
            setBusy(false)
        }
    }

    const move = (index, delta) => {
        const order = items.map(i => i.id)
        const [moved] = order.splice(index, 1)
        order.splice(index + delta, 0, moved)
        mutate(() => api(`/lists/${list.id}/items/reorder`, { method: 'PUT', body: { order } }),
               'Could not reorder. Please try again.')
    }

    const removeItem = (itemId) =>
        mutate(() => api(`/lists/${list.id}/items/${itemId}`, { method: 'DELETE' }),
               'Could not remove the album. Please try again.')

    const deleteList = async () => {
        if (!window.confirm(`Delete "${list.title}"? This can't be undone.`)) return
        try {
            await api(`/lists/${list.id}`, { method: 'DELETE' })
            navigate('/lists')
        } catch {
            window.alert('Could not delete the list. Please try again.')
        }
    }

    return (
        <div className='list-detail'>
            {editing ? (
                <EditListForm list={list} onDone={(saved) => { setEditing(false); if (saved) reload() }} />
            ) : (
                <header className='list-detail__header'>
                    <p className='list-detail__label'>
                        List by <Link to={`/users/${list.user_id}`}>{list.username}</Link>
                        {!list.is_public && <span className='list-detail__badge'>Private</span>}
                    </p>
                    <h1 className='list-detail__title'>{list.title}</h1>
                    {list.description && <p className='list-detail__description'>{list.description}</p>}
                    {isOwner && (
                        <div className='list-detail__owner'>
                            <button className='review-item__edit-btn' onClick={() => setEditing(true)}>Edit</button>
                            <button className='review-item__delete-btn' onClick={deleteList}>Delete list</button>
                        </div>
                    )}
                </header>
            )}

            {items.length === 0 ? (
                <p className='feed__status'>
                    {isOwner ? 'No albums yet. Use "+ Add to list" on any album page.' : 'This list is empty.'}
                </p>
            ) : (
                <ol className='list-items'>
                    {items.map((item, i) => (
                        <li key={item.id} className='list-item'>
                            <span className='list-item__pos'>{i + 1}</span>
                            <Link to={`/albums/${item.album.mbid}`} className='list-item__cover-link'>
                                {item.album.cover_url
                                    ? <img src={item.album.cover_url} alt='' className='list-item__cover' loading='lazy' />
                                    : <span className='list-item__cover list-card__cover-empty' />}
                            </Link>
                            <div className='list-item__info'>
                                <Link to={`/albums/${item.album.mbid}`} className='list-item__title'>{item.album.title}</Link>
                                <span className='list-item__artists'>
                                    {item.album.artists.map(a => a.name).join(', ')}
                                    {item.album.release_year && ` · ${item.album.release_year}`}
                                </span>
                                {item.note && <p className='list-item__note'>{item.note}</p>}
                            </div>
                            {isOwner && (
                                <div className='list-item__controls'>
                                    <button onClick={() => move(i, -1)} disabled={busy || i === 0} aria-label='Move up'>↑</button>
                                    <button onClick={() => move(i, 1)} disabled={busy || i === items.length - 1} aria-label='Move down'>↓</button>
                                    <button onClick={() => removeItem(item.id)} disabled={busy} aria-label='Remove' className='list-item__remove'>✕</button>
                                </div>
                            )}
                        </li>
                    ))}
                </ol>
            )}
        </div>
    )
}

export default ListDetails
