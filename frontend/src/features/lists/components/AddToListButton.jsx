import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/context/useAuth.js';
import { useApi } from '@/utils/useApi.js';
import api from '@/api/client.js';
import './Lists.css';

/** Album page dropdown: add this album to one of your lists, or a new one. */
function AddToListButton({ mbid }) {
    const { user, isAuthenticated, openLogin } = useAuth()
    const [open, setOpen] = useState(false)
    const [results, setResults] = useState({})   // listId -> 'added' | 'exists' | 'error'
    const [newTitle, setNewTitle] = useState('')
    const [creating, setCreating] = useState(false)
    const wrapRef = useRef(null)

    const lists = useApi(open && user ? `/users/${user.id}/lists?per_page=50` : null)

    useEffect(() => {
        if (!open) return
        const onClick = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false) }
        document.addEventListener('mousedown', onClick)
        return () => document.removeEventListener('mousedown', onClick)
    }, [open])

    const addTo = async (listId) => {
        try {
            await api(`/lists/${listId}/items`, { method: 'POST', body: { album_mbid: mbid } })
            setResults(r => ({ ...r, [listId]: 'added' }))
        } catch (err) {
            setResults(r => ({ ...r, [listId]: /already/i.test(err.message) ? 'exists' : 'error' }))
        }
    }

    const createAndAdd = async (e) => {
        e.preventDefault()
        if (!newTitle.trim()) return
        setCreating(true)
        try {
            const { id } = await api('/lists', { method: 'POST', body: { title: newTitle.trim() } })
            await addTo(id)
            setNewTitle('')
            lists.reload()
        } catch {
            window.alert('Could not create the list. Please try again.')
        } finally {
            setCreating(false)
        }
    }

    const label = { added: '✓ Added', exists: 'Already here', error: 'Failed' }

    return (
        <div className='add-to-list' ref={wrapRef}>
            <button
                type='button'
                className='album-detail-review-btn'
                onClick={() => (isAuthenticated ? setOpen(o => !o) : openLogin())}
                aria-expanded={open}
            >
                + Add to list
            </button>

            {open && (
                <div className='add-to-list__panel'>
                    {lists.loading && !lists.data && <p className='add-to-list__status'>Loading your lists…</p>}
                    {lists.data?.lists?.length === 0 && <p className='add-to-list__status'>You don't have any lists yet.</p>}
                    {lists.data?.lists?.map(l => (
                        <button
                            key={l.id}
                            type='button'
                            className='add-to-list__item'
                            onClick={() => addTo(l.id)}
                            disabled={results[l.id] === 'added'}
                        >
                            <span>{l.title}{!l.is_public && <span className='add-to-list__private'> · private</span>}</span>
                            <span className='add-to-list__result'>{label[results[l.id]] || `${l.item_count}`}</span>
                        </button>
                    ))}
                    <form className='add-to-list__new' onSubmit={createAndAdd}>
                        <input
                            className='add-to-list__input'
                            placeholder='New list name'
                            value={newTitle}
                            maxLength={255}
                            onChange={e => setNewTitle(e.target.value)}
                        />
                        <button type='submit' className='comment-form__submit' disabled={!newTitle.trim() || creating}>
                            Create
                        </button>
                    </form>
                </div>
            )}
        </div>
    )
}

export default AddToListButton
