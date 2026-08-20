import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

import Login from '../pages/Login/Login'
import Register from '../pages/Register/Register'
import Dashboard from '../pages/Dashboard/Dashboard'
import Profile from '../pages/Profile/Profile'
import BlogList from '../pages/BlogList/BlogList'
import BlogDetail from '../pages/BlogDetail/BlogDetail'
import BlogEditor from '../pages/BlogEditor/BlogEditor'

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

      <Route path="/" element={
        <ProtectedRoute><Dashboard /></ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute><Profile /></ProtectedRoute>
      } />
      <Route path="/blogs" element={
        <ProtectedRoute><BlogList /></ProtectedRoute>
      } />
      <Route path="/blogs/new" element={
        <ProtectedRoute><BlogEditor /></ProtectedRoute>
      } />
      <Route path="/blogs/:id" element={
        <ProtectedRoute><BlogDetail /></ProtectedRoute>
      } />
      <Route path="/blogs/:id/edit" element={
        <ProtectedRoute><BlogEditor /></ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default Router
