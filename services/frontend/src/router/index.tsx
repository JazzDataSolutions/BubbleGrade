import { createBrowserRouter, Navigate } from 'react-router-dom'
import Layout from '../components/Layout/Layout'
import Dashboard from '../pages/Dashboard/Dashboard'
import ScanHistory from '../pages/ScanHistory/ScanHistory'
import Templates from '../pages/Templates/Templates'
import Settings from '../pages/Settings/Settings'
import ScanDetail from '../pages/ScanDetail/ScanDetail'
import Login from '../pages/Auth/Login'
import { ProtectedRoute } from '../components/Auth/ProtectedRoute'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />
      },
      {
        path: 'dashboard',
        element: <Dashboard />
      },
      {
        path: 'history',
        element: <ScanHistory />
      },
      {
        path: 'scan/:scanId',
        element: <ScanDetail />
      },
      {
        path: 'templates',
        element: <Templates />
      },
      {
        path: 'settings',
        element: <Settings />
      }
    ]
  }
])