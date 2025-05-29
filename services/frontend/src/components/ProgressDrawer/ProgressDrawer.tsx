import React, { useState, useEffect } from 'react'
import { Drawer, List } from 'antd'
import 'antd/dist/reset.css'

export interface ProgressDrawerProps {
  visible: boolean
  onClose: () => void
  scanId: string
}

const ProgressDrawer: React.FC<ProgressDrawerProps> = ({ visible, onClose, scanId }) => {
  const [messages, setMessages] = useState<string[]>([])

  useEffect(() => {
    if (!visible) return
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws'
    const ws = new WebSocket(wsUrl)
    ws.onopen = () => console.log('WebSocket connected')
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.scan_id === scanId) {
          const text = data.stage || data.status || JSON.stringify(data)
          setMessages(prev => [...prev, text])
        }
      } catch {}
    }
    ws.onerror = (err) => console.error('WebSocket error', err)
    return () => { ws.close() }
  }, [visible, scanId])

  return (
    <Drawer
      title="Progreso del escaneo"
      placement="right"
      onClose={onClose}
      open={visible}
      width={320}
    >
      <List
        size="small"
        bordered
        dataSource={messages}
        renderItem={(item, idx) => <List.Item key={idx}>{item}</List.Item>}
      />
    </Drawer>
  )
}

export default ProgressDrawer