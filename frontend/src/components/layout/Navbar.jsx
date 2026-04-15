import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext.jsx';
import { getAvatarColor } from '@/utils/avatar.js';
import LoginModal from './LoginModal.jsx';
import RegisterModal from './RegisterModal.jsx';
import api from '@/api/client.js';
import './Navbar.css';

function SearchDropdown({ results, query, onSelect }) {
    const hasAlbums = results?.albums?.length > 0;
    const hasArtists = results?.artists?.length > 0;
    const isEmpty = results && !hasAlbums && !hasArtists;

    if (!results) return null;

    return (
        <div className='search-dropdown'>
            {isEmpty && (
                <p className='search-dropdown__empty'>No results for "{query}"</p>
            )}

            {hasArtists && (
                <div className='search-dropdown__section'>
                    <span className='search-dropdown__label'>Artists</span>
                    {results.artists.map(artist => (
                        <Link
                            key={artist.mbid}
                            to={`/artists/${artist.mbid}`}
                            className='search-dropdown__item'
                            onClick={onSelect}
                        >
                            <div className='search-dropdown__thumb search-dropdown__thumb--round'>
                                {artist.image_url
                                    ? <img src={artist.image_url} alt={artist.name} onError={e => e.target.style.display='none'} />
                                    : <span>{artist.name.charAt(0)}</span>
                                }
                            </div>
                            <div className='search-dropdown__info'>
                                <span className='search-dropdown__title'>{artist.name}</span>
                                <span className='search-dropdown__sub'>Artist</span>
                            </div>
                        </Link>
                    ))}
                </div>
            )}

            {hasAlbums && (
                <div className='search-dropdown__section'>
                    <span className='search-dropdown__label'>Albums</span>
                    {results.albums.map(album => (
                        <Link
                            key={album.mbid}
                            to={`/albums/${album.mbid}`}
                            className='search-dropdown__item'
                            onClick={onSelect}
                        >
                            <div className='search-dropdown__thumb'>
                                {album.cover_url
                                    ? <img src={album.cover_url} alt={album.title} onError={e => e.target.style.display='none'} />
                                    : <span>{album.title.charAt(0)}</span>
                                }
                            </div>
                            <div className='search-dropdown__info'>
                                <span className='search-dropdown__title'>{album.title}</span>
                                <span className='search-dropdown__sub'>
                                    {album.artists?.map(a => a.name).join(', ')}
                                    {album.release_year ? ` · ${album.release_year}` : ''}
                                </span>
                            </div>
                        </Link>
                    ))}
                </div>
            )}

            {(hasAlbums || hasArtists) && (
                <div className='search-dropdown__footer'>
                    Press Enter to see all results
                </div>
            )}
        </div>
    );
}

function Navbar() {
    const { user, isAuthenticated, loading, logout } = useAuth();
    const navigate = useNavigate();

    const [searchQuery, setSearchQuery] = useState('');
    const [dropdownResults, setDropdownResults] = useState(null);
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [showLogin, setShowLogin] = useState(false);
    const [showRegister, setShowRegister] = useState(false);

    const searchRef = useRef(null);
    const wrapperRef = useRef(null);
    const debounceRef = useRef(null);

    // Close dropdown on outside click
    useEffect(() => {
        const handleClick = (e) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    const fetchDropdown = useCallback((q) => {
        if (!q.trim()) {
            setDropdownResults(null);
            setDropdownOpen(false);
            return;
        }
        api(`/search?q=${encodeURIComponent(q)}`)
            .then(data => {
                setDropdownResults(data);
                setDropdownOpen(true);
            })
            .catch(() => {
                setDropdownResults(null);
            });
    }, []);

    const handleSearchChange = (e) => {
        const val = e.target.value;
        setSearchQuery(val);

        clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => fetchDropdown(val), 250);
    };

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        const q = searchQuery.trim();
        if (!q) return;
        setDropdownOpen(false);
        setSearchQuery('');
        navigate(`/search?q=${encodeURIComponent(q)}`);
        searchRef.current?.blur();
    };

    const handleSelect = () => {
        setDropdownOpen(false);
        setSearchQuery('');
    };

    const handleLogout = async () => {
        await logout();
        navigate('/', { replace: true });
    };

    const switchToRegister = () => { setShowLogin(false); setShowRegister(true); };
    const switchToLogin = () => { setShowRegister(false); setShowLogin(true); };

    if (loading) return null;

    const avatarColor = user ? getAvatarColor(user.username) : null;

    return (
        <>
            <nav className='navbar'>
                <Link to={isAuthenticated ? '/albums' : '/'} className='navbar__logo'>
                    Nothing
                </Link>

                {isAuthenticated ? (
                    <>
                        <div className='navbar__links'>
                            <Link to='/albums' className='navbar__link'>Albums</Link>
                        </div>

                        {/* ── Search with dropdown ── */}
                        <div className='navbar__search-wrap' ref={wrapperRef}>
                            <form className='navbar__search' onSubmit={handleSearchSubmit}>
                                <input
                                    ref={searchRef}
                                    type='text'
                                    className='navbar__search-input'
                                    placeholder='Search albums, artists…'
                                    value={searchQuery}
                                    onChange={handleSearchChange}
                                    onFocus={() => dropdownResults && setDropdownOpen(true)}
                                    autoComplete='off'
                                />
                                <button type='submit' className='navbar__search-btn' aria-label='Search'>
                                    <svg width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2.5' strokeLinecap='round' strokeLinejoin='round'>
                                        <circle cx='11' cy='11' r='8' />
                                        <line x1='21' y1='21' x2='16.65' y2='16.65' />
                                    </svg>
                                </button>
                            </form>

                            {dropdownOpen && (
                                <SearchDropdown
                                    results={dropdownResults}
                                    query={searchQuery}
                                    onSelect={handleSelect}
                                />
                            )}
                        </div>

                        <div className='navbar__user'>
                            <Link
                                to={`/users/${user.id}`}
                                className='navbar__avatar'
                                style={{ borderColor: avatarColor, color: avatarColor }}
                                title={user.username}
                            >
                                {user.username.charAt(0).toUpperCase()}
                            </Link>
                            <Link to={`/users/${user.id}`} className='navbar__username'>
                                {user.username}
                            </Link>
                            <button className='navbar__logout' onClick={handleLogout}>
                                Logout
                            </button>
                        </div>
                    </>
                ) : (
                    <div className='navbar__auth'>
                        <button className='navbar__auth-link' onClick={() => setShowLogin(true)}>Login</button>
                        <button className='navbar__auth-btn' onClick={() => setShowRegister(true)}>Register</button>
                    </div>
                )}
            </nav>

            {showLogin && <LoginModal onClose={() => setShowLogin(false)} onSwitchToRegister={switchToRegister} />}
            {showRegister && <RegisterModal onClose={() => setShowRegister(false)} onSwitchToLogin={switchToLogin} />}
        </>
    );
}

export default Navbar;