import { Route, Routes } from 'react-router-dom';
import './App.css';
import { useAuth } from '@/context/useAuth.js';
import Navbar from '@/components/layout/Navbar.jsx';
import { AlbumList, AlbumDetails } from '@/features/albums';
import { ArtistList, ArtistDetails } from '@/features/artists';
import { UserProfile } from '@/features/users';
import ListsPage from '@/features/lists/components/ListsPage.jsx';
import ListDetails from '@/features/lists/components/ListDetails.jsx';
import NotificationsPage from '@/features/notifications/components/NotificationsPage.jsx';
import SearchPage from '@/pages/SearchPage.jsx';
import Home from '@/pages/Home.jsx';

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
          <Route path='/' element={<Home />} />
          <Route path='/search' element={<SearchPage />} />
          <Route path='/albums' element={<AlbumList />} />
          <Route path='/albums/:mbid' element={<AlbumDetails />} />
          <Route path='/artists' element={<ArtistList />} />
          <Route path='/artists/:mbid' element={<ArtistDetails />} />
          <Route path='/users/:user_id' element={<UserProfile />} />
          <Route path='/lists' element={<ListsPage />} />
          <Route path='/lists/:id' element={<ListDetails />} />
          <Route path='/notifications' element={<NotificationsPage />} />
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
