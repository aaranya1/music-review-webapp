const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

let isRefreshing = false;
let refreshPromise = null;

const getAccessToken = () => localStorage.getItem('accessToken');

const setAccessToken = (token) => {
    localStorage.setItem('accessToken', token);
}

const clearAccessToken = () => {
    localStorage.removeItem('accessToken');
}

const refreshAccessToken = async () => {
    if(isRefreshing) return refreshPromise;

    isRefreshing = true;
    refreshPromise = fetch(`${API_BASE_URL}/refresh`, {
        method: 'POST',
        credentials: 'include'
    })
    .then(async response => {
        if(!response.ok){
            throw new Error('Refresh failed');
        }
        
        const data = await response.json();
        setAccessToken(data.access_token);
        return data.access_token;
    })
    .finally(() => {
        isRefreshing = false;
        refreshPromise = null;
    })

    return refreshPromise;
}

const api = async (endpoint, {method='GET', body} = {}) => {
    const token = getAccessToken();
    const options = {
        method,
        headers: {},
        credentials: 'include'
    };

    if(body){
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }

    if(token){
        options.headers['Authorization'] = `Bearer ${token}`;   
    }

    let response = await fetch(`${API_BASE_URL}${endpoint}`, options);

    if(response.status === 401 && token){
        try{
            const newToken = await refreshAccessToken();
            response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers: {
                    ...options.headers,
                    'Authorization': `Bearer ${newToken}`
                }
            });
        }  catch(err){
            clearAccessToken();
            throw err;
        }
    }

    if(!response.ok){
        const err = await response.json().catch(() => ({}));
        throw new Error(err.message || 'API request failed');
    }

    if(method == 'DELETE'){
        return true;
    }

    return response.json();    
};

export default api;

