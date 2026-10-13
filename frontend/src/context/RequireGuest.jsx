import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/useAuth.js'

function RequireGuest({children}){
    const { isAuthenticated } = useAuth()

    return (
        isAuthenticated ?
            <Navigate to='/albums' /> :
            children
    )
} 

export default RequireGuest