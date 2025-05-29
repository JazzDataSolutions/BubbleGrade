import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '../store'
import { WebSocketMessage } from '../types'

export const useWebSocket = () => {
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  
  const { updateScan, addNotification, isAuthenticated } = useAppStore()

  const connect = useCallback(() => {
    if (!isAuthenticated) return

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws`
      
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        console.log('🔗 WebSocket connected')
        reconnectAttempts.current = 0
        addNotification({
          type: 'success',
          title: 'Connected',
          message: 'Real-time updates enabled',
          duration: 3000
        })
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleWebSocketMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.current.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason)
        
        if (!event.wasClean && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            console.log(`🔄 Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})`)
            connect()
          }, delay)
        }
      }

      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        addNotification({
          type: 'error',
          title: 'Connection Error',
          message: 'Failed to connect to real-time updates'
        })
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [isAuthenticated, addNotification])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (ws.current) {
      ws.current.close(1000, 'Component unmounting')
      ws.current = null
    }
  }, [])

  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'scan_update':
        updateScan(message.scanId, { 
          status: message.data.status 
        })
        break
        
      case 'scan_complete':
        updateScan(message.scanId, {
          status: 'COMPLETED',
          score: message.data.score,
          answers: message.data.answers,
          processedTime: new Date().toISOString()
        })
        addNotification({
          type: 'success',
          title: 'Scan Complete!',
          message: `Scan processed with ${message.data.score}% score`
        })
        break
        
      case 'scan_error':
        updateScan(message.scanId, {
          status: 'ERROR',
          errorMessage: message.data.error
        })
        addNotification({
          type: 'error',
          title: 'Scan Failed',
          message: message.data.error || 'Processing failed'
        })
        break
        
      default:
        console.warn('Unknown WebSocket message type:', message.type)
    }
  }, [updateScan, addNotification])

  useEffect(() => {
    if (isAuthenticated) {
      connect()
    } else {
      disconnect()
    }

    return disconnect
  }, [isAuthenticated, connect, disconnect])

  return {
    isConnected: ws.current?.readyState === WebSocket.OPEN,
    connect,
    disconnect
  }
}