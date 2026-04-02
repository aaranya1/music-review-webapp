import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import './AuthModal.css';

function LoginModal({ onClose, onSwitchToRegister }) {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState(null)
    const [submitting, setSubmitting] = useState(false)

    const { login } = useAuth()
    const navigate = useNavigate()
    const location = useLocation()

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
            await login(username, password)
            onClose()
            const from = location.state?.from?.pathname
            navigate(from || '/albums', { replace: true })
        } catch {
            setError('Incorrect username or password.')
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div className='auth-backdrop' onClick={handleBackdropClick}>
            <div className='auth-modal'>
                <button className='auth-modal__close' onClick={onClose} aria-label='Close'>✕</button>

                <p className='auth-modal__label'>Welcome back</p>
                <h2 className='auth-modal__title'>Login</h2>

                <div className='auth-modal__divider' />

                <form onSubmit={handleSubmit}>
                    <div className='auth-modal__field'>
                        <label className='auth-modal__field-label' htmlFor='login-username'>Username</label>
                        <input
                            id='login-username'
                            type='text'
                            className='auth-modal__input'
                            placeholder='Your username'
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            disabled={submitting}
                            required
                            autoFocus
                        />
                    </div>

                    <div className='auth-modal__field'>
                        <label className='auth-modal__field-label' htmlFor='login-password'>Password</label>
                        <input
                            id='login-password'
                            type='password'
                            className='auth-modal__input'
                            placeholder='Your password'
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
                        disabled={submitting || !username || !password}
                    >
                        {submitting ? 'Logging in…' : 'Login'}
                    </button>
                </form>

                <p className='auth-modal__switch'>
                    Don't have an account?{' '}
                    <button className='auth-modal__switch-btn' onClick={onSwitchToRegister}>
                        Register
                    </button>
                </p>
            </div>
        </div>
    )
}

export default LoginModal