import React, { createContext, useContext, useEffect, useState } from 'react';
import api from '../api/client.js';
const AuthContext = createContext()

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    const isAuthenticated = !!user

    useEffect(() => {
        const token = localStorage.getItem('accessToken')
        if(!token){
            setLoading(false)
            return
        }

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
            loading
        }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth(){
    return useContext(AuthContext)
}