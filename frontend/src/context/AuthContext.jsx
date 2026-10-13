import React, { useEffect, useState } from 'react';
import api from '../api/client.js';
import { AuthContext } from './useAuth.js';

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    // Only "loading" if there's a stored token to validate; otherwise we already know
    const [loading, setLoading] = useState(() => !!localStorage.getItem('accessToken'))

    // Which auth dialog is open ('login' | 'register' | null). Lives here so any
    // component can prompt a logged-out visitor to log in.
    const [authModal, setAuthModal] = useState(null)

    const isAuthenticated = !!user

    useEffect(() => {
        if (!localStorage.getItem('accessToken')) return

        api('/me')
            .then(data => setUser(data))
            .catch(() => {
                setUser(null)
                localStorage.removeItem('accessToken')
            })
            .finally(() => setLoading(false))
    }, [])

    const register = async (username, email, password) => {
        await api('/register', {
            method: 'POST',
            body: { username, email, password }
        })
        
        await login(username, password)
    }

    const login = async (username, password) => {
        const data = await api('/login', { 
            method: 'POST', 
            body: { username, password } 
        })
        localStorage.setItem('accessToken', data.access_token)

        const me = await api('/me')
        setUser(me)
    }

    const logout = async () => {
        await api('/logout', {
            method: 'POST',
            body: {}
        })
        localStorage.removeItem('accessToken')
        setUser(null)
    }

    return (
        <AuthContext.Provider value={{
            user,
            isAuthenticated,
            register,
            login,
            logout,
            loading,
            authModal,
            openLogin: () => setAuthModal('login'),
            openRegister: () => setAuthModal('register'),
            closeAuthModal: () => setAuthModal(null),
        }}>
            {children}
        </AuthContext.Provider>
    )
}
