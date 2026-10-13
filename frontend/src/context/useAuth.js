import { createContext, useContext } from 'react';

// Lives outside AuthContext.jsx so that file exports only components,
// which React Fast Refresh needs to hot-reload it.
export const AuthContext = createContext(null)

export function useAuth() {
    return useContext(AuthContext)
}
