import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

function RequireAuth({children}){
    const { isAuthenticated } = useAuth()
    const location = useLocation()

    return (
        isAuthenticated ?
            children :
            <Navigate to='/login' state={{from: location}}  replace />
    )
} 

export default RequireAuth