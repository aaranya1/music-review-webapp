import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

function RequireGuest({children}){
    const { isAuthenticated } = useAuth()

    return (
        isAuthenticated ?
            <Navigate to='/albums' /> :
            children
    )
} 

export default RequireGuest