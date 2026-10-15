import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

import Login from '../pages/Login/Login'
import Register from '../pages/Register/Register'
import Dashboard from '../pages/Dashboard/Dashboard'
import Profile from '../pages/Profile/Profile'
import BlogList from '../pages/BlogList/BlogList'
import BlogDetail from '../pages/BlogDetail/BlogDetail'
import BlogEditor from '../pages/BlogEditor/BlogEditor'

// v2 新页面
import Couple from '../pages/Couple/Couple'
import Anniversaries from '../pages/Anniversaries/Anniversaries'
import Albums from '../pages/Albums/Albums'
import Timeline from '../pages/Timeline/Timeline'

import AppLayout from '../components/layout/AppLayout'

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

function Router() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/couple" element={<Couple />} />
        <Route path="/blogs" element={<BlogList />} />
        <Route path="/blogs/new" element={<BlogEditor />} />
        <Route path="/blogs/:id" element={<BlogDetail />} />
        <Route path="/blogs/:id/edit" element={<BlogEditor />} />
        <Route path="/anniversaries" element={<Anniversaries />} />
        <Route path="/albums" element={<Albums />} />
        <Route path="/timeline" element={<Timeline />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default Router
