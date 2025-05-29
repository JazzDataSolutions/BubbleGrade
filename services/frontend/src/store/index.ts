import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { Scan, User, ExamTemplate } from '../types'

interface AppState {
  // Auth
  user: User | null
  isAuthenticated: boolean
  token: string | null
  
  // Scans
  scans: Scan[]
  activeScan: Scan | null
  isUploading: boolean
  
  // Templates
  templates: ExamTemplate[]
  activeTemplate: ExamTemplate | null
  
  // UI
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  notifications: Notification[]
  
  // Actions
  setUser: (user: User | null) => void
  login: (token: string, user: User) => void
  logout: () => void
  
  addScan: (scan: Scan) => void
  updateScan: (scanId: string, updates: Partial<Scan>) => void
  setScans: (scans: Scan[]) => void
  setActiveScan: (scan: Scan | null) => void
  setIsUploading: (uploading: boolean) => void
  
  setTemplates: (templates: ExamTemplate[]) => void
  setActiveTemplate: (template: ExamTemplate | null) => void
  
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
}

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        user: null,
        isAuthenticated: false,
        token: null,
        scans: [],
        activeScan: null,
        isUploading: false,
        templates: [],
        activeTemplate: null,
        sidebarOpen: true,
        theme: 'light',
        notifications: [],

        // Auth actions
        setUser: (user) => set({ user }),
        login: (token, user) => set({ 
          token, 
          user, 
          isAuthenticated: true 
        }),
        logout: () => set({ 
          token: null, 
          user: null, 
          isAuthenticated: false 
        }),

        // Scan actions
        addScan: (scan) => set((state) => ({ 
          scans: [scan, ...state.scans] 
        })),
        updateScan: (scanId, updates) => set((state) => ({
          scans: state.scans.map(scan => 
            scan.id === scanId ? { ...scan, ...updates } : scan
          ),
          activeScan: state.activeScan?.id === scanId 
            ? { ...state.activeScan, ...updates } 
            : state.activeScan
        })),
        setScans: (scans) => set({ scans }),
        setActiveScan: (scan) => set({ activeScan: scan }),
        setIsUploading: (uploading) => set({ isUploading: uploading }),

        // Template actions
        setTemplates: (templates) => set({ templates }),
        setActiveTemplate: (template) => set({ activeTemplate: template }),

        // UI actions
        toggleSidebar: () => set((state) => ({ 
          sidebarOpen: !state.sidebarOpen 
        })),
        setTheme: (theme) => set({ theme }),
        addNotification: (notification) => set((state) => ({
          notifications: [
            ...state.notifications,
            { ...notification, id: crypto.randomUUID() }
          ]
        })),
        removeNotification: (id) => set((state) => ({
          notifications: state.notifications.filter(n => n.id !== id)
        }))
      }),
      {
        name: 'bubblegrade-storage',
        partialize: (state) => ({
          token: state.token,
          user: state.user,
          isAuthenticated: state.isAuthenticated,
          theme: state.theme,
          sidebarOpen: state.sidebarOpen
        })
      }
    )
  )
)