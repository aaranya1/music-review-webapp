import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import './AuthModal.css';

function RegisterModal({ onClose, onSwitchToLogin }) {
    const [username, setUsername] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState(null)
    const [submitting, setSubmitting] = useState(false)

    const { register } = useAuth()
    const navigate = useNavigate()

    useEffect(() => {
        const handleKey = (e) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [onClose])

    useEffect(() => {
        document.body.style.overflow = 'hidden'
        return () => { document.body.style.overflow = '' }
    }, [])

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) onClose()
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSubmitting(true)
        setError(null)
        try {
            await register(username, email, password)
            onClose()
            navigate('/albums', { replace: true })
        } catch (err) {
            setError(err.message || 'Registration failed.')
        } finally {
            setSubmitting(false)
        }
    }

    const isValid = username && email && password

    return (
        <div className='auth-backdrop' onClick={handleBackdropClick}>
            <div className='auth-modal'>
                <button className='auth-modal__close' onClick={onClose} aria-label='Close'>✕</button>

                <p className='auth-modal__label'>Create an Account</p>
                <h2 className='auth-modal__title'>Create Account</h2>

                <div className='auth-modal__divider' />

                <form onSubmit={handleSubmit}>
                    <div className='auth-modal__field'>
                        <label className='auth-modal__field-label' htmlFor='reg-username'>Username</label>
                        <input
                            id='reg-username'
                            type='text'
                            className='auth-modal__input'
                            placeholder='Choose a username'
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            disabled={submitting}
                            required
                            autoFocus
                        />
                    </div>

                    <div className='auth-modal__field'>
                        <label className='auth-modal__field-label' htmlFor='reg-email'>Email</label>
                        <input
                            id='reg-email'
                            type='email'
                            className='auth-modal__input'
                            placeholder='Your email address'
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            disabled={submitting}
                            required
                        />
                    </div>

                    <div className='auth-modal__field'>
                        <label className='auth-modal__field-label' htmlFor='reg-password'>Password</label>
                        <input
                            id='reg-password'
                            type='password'
                            className='auth-modal__input'
                            placeholder='Create a password'
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            disabled={submitting}
                            required
                        />
                    </div>

                    {error && <p className='auth-modal__error'>{error}</p>}

                    <button
                        type='submit'
                        className='auth-modal__submit'
                        disabled={submitting || !isValid}
                    >
                        {submitting ? 'Creating account…' : 'Create Account'}
                    </button>
                </form>

                <p className='auth-modal__switch'>
                    Already have an account?{' '}
                    <button className='auth-modal__switch-btn' onClick={onSwitchToLogin}>
                        Login
                    </button>
                </p>
            </div>
        </div>
    )
}

export default RegisterModal