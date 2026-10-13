import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipLoader } from 'react-spinners';
import { useAuth } from '@/context/useAuth.js';
import { useApi } from '@/utils/useApi.js';
import api from '@/api/client.js';
import ListCard from './ListCard.jsx';
import './Lists.css';

function NewListForm({ onCancel }) {
    const navigate = useNavigate()
    const [title, setTitle] = useState('')
    const [description, setDescription] = useState('')
    const [isPublic, setIsPublic] = useState(true)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)

    const submit = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError(null)
        try {
            const { id } = await api('/lists', {
                method: 'POST',
                body: { title: title.trim(), description: description.trim() || null, is_public: isPublic },
            })
            navigate(`/lists/${id}`)
        } catch (err) {
            setError(err.message || 'Could not create the list.')
            setSaving(false)
        }
    }

    return (
        <form className='list-form' onSubmit={submit}>
            <input className='list-form__input' placeholder='List name' value={title} maxLength={255}
                   onChange={e => setTitle(e.target.value)} autoFocus />
            <textarea className='list-form__input' placeholder='Description (optional)' value={description}
                      maxLength={2000} rows={2} onChange={e => setDescription(e.target.value)} />
            <label className='list-form__check'>
                <input type='checkbox' checked={isPublic} onChange={e => setIsPublic(e.target.checked)} />
                Public
            </label>
            <div className='list-form__row'>
                {error && <span className='comment-form__error'>{error}</span>}
                <button type='button' className='list-form__cancel' onClick={onCancel}>Cancel</button>
                <button type='submit' className='comment-form__submit' disabled={!title.trim() || saving}>
                    {saving ? 'Creating…' : 'Create list'}
                </button>
            </div>
        </form>
    )
}

function ListsPage() {
    const { isAuthenticated, openLogin } = useAuth()
    const [page, setPage] = useState(1)
    const [creating, setCreating] = useState(false)
    const { data, error, loading, reload } = useApi(`/lists?page=${page}&per_page=24`)
    const lists = data?.lists || []
    const totalPages = data?.total_pages || 1

    return (
        <div className='lists-page'>
            <div className='lists-page__header'>
                <h2 className='lists-page__title'>Lists</h2>
                {!creating && (
                    <button className='album-detail-review-btn' onClick={() => (isAuthenticated ? setCreating(true) : openLogin())}>
                        + New list
                    </button>
                )}
            </div>

            {creating && <NewListForm onCancel={() => setCreating(false)} />}

            {loading && !data && <div className='feed__loader'><ClipLoader color='#c8a96e' size={32} aria-label='Loading' /></div>}
            {error && (
                <p className='feed__status'>Couldn't load lists. <button className='feed__link' onClick={reload}>Retry</button></p>
            )}
            {data && lists.length === 0 && <p className='feed__status'>No public lists yet. Be the first to make one.</p>}

            <div className='list-grid'>
                {lists.map(l => <ListCard key={l.id} list={l} />)}
            </div>

            {totalPages > 1 && (
                <div className='pagination'>
                    <button onClick={() => setPage(p => p - 1)} disabled={page === 1}>← Prev</button>
                    <span className='page-label'>{page} / {totalPages}</span>
                    <button onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>Next →</button>
                </div>
            )}
        </div>
    )
}

export default ListsPage
