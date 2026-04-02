import React, { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import './App.css';
import { useAuth } from './context/AuthContext.jsx';
import RequireAuth from './context/RequireAuth.jsx';
import RequireGuest from './context/RequireGuest.jsx';
import Navbar from './components/Nav/Navbar.jsx';
import AlbumList from './components/Album/AlbumList.jsx';
import ArtistList from './components/Artist/ArtistList.jsx';
import ArtistDetails from './components/Artist/ArtistDetails.jsx';
import AlbumDetails from './components/Album/AlbumDetails.jsx';
import UserProfile from './components/User/UserProfile.jsx';
import SearchPage from './pages/SearchPage.jsx';

function App() {

  const context = useAuth()

  if(context.loading){
    return <div>Loading...</div>
  }

  return (
    <>
      <div>
        <Navbar />
        <Routes>
          <Route path='/search' element={<RequireAuth><SearchPage /></RequireAuth>} /> 
          <Route path='/albums' element={<RequireAuth><AlbumList /></RequireAuth>} />
          <Route path='/albums/:mbid' element={<RequireAuth><AlbumDetails /></RequireAuth>} />
          <Route path='/artists' element={<RequireAuth><ArtistList /></RequireAuth>} />
          <Route path='/artists/:mbid' element={<RequireAuth><ArtistDetails /></RequireAuth>} />
          <Route path='/users/:user_id' element={<RequireAuth><UserProfile /></RequireAuth>} />
          <Route path='*' element={
            <div style={{ textAlign: 'center', padding: '6rem 2rem', fontFamily: 'var(--font-body)', color: '#706c68' }}>
              <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '2rem', color: '#ddd9d1', marginBottom: '0.5rem' }}>404</h2>
              <p>This page doesn't exist.</p>
            </div>
          } />
        </Routes>
      </div>
    </>
  )
}

export default App
