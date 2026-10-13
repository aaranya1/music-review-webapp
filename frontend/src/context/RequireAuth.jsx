import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/useAuth.js'

function RequireAuth({children}){
    const { isAuthenticated } = useAuth()
    const location = useLocation()

    return (
        isAuthenticated ?
            children :
            <Navigate to='/' state={{from: location}}  replace />
    )
}

export default RequireAuth