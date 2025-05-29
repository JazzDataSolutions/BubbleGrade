import React from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { NotificationContainer } from '../Notifications/NotificationContainer'
import { useWebSocket } from '../../hooks/useWebSocket'
import { useAppStore } from '../../store'
import './Layout.css'

export const Layout: React.FC = () => {
  const { sidebarOpen, theme } = useAppStore()
  useWebSocket() // Initialize WebSocket connection

  return (
    <div className={`layout ${theme}`} data-sidebar-open={sidebarOpen}>
      <Sidebar />
      <div className="layout-main">
        <Header />
        <main className="layout-content">
          <Outlet />
        </main>
      </div>
      <NotificationContainer />
    </div>
  )
}