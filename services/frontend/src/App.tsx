import { useState, useCallback } from 'react'
import './App.css'

interface ScanResult {
  id: string
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'ERROR'
  score?: number
  filename?: string
}

function App() {
  const [scans, setScans] = useState<ScanResult[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    files.forEach(file => uploadFile(file))
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach(file => uploadFile(file))
  }, [])

  const uploadFile = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/scans', {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        const result = await response.json()
        setScans(prev => [...prev, { 
          ...result, 
          filename: file.name,
          status: 'PROCESSING' 
        }])
        
        setTimeout(() => {
          setScans(prev => prev.map(scan => 
            scan.id === result.id 
              ? { ...scan, status: 'COMPLETED', score: 85 }
              : scan
          ))
        }, 2000)
      }
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  const exportScan = async (scanId: string) => {
    try {
      const response = await fetch(`/api/exports/${scanId}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${scanId}.xlsx`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🫧 BubbleGrade</h1>
        <p>Optical Mark Recognition for Bubble Sheets</p>
      </header>

      <main className="main">
        <div 
          className={`drop-zone ${isDragging ? 'dragging' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <div className="drop-content">
            <div className="drop-icon">📄</div>
            <h3>Drop your bubble sheets here</h3>
            <p>or</p>
            <label className="file-input-label">
              <input 
                type="file" 
                multiple 
                accept="image/*,.pdf"
                onChange={handleFileInput}
                className="file-input"
              />
              Choose Files
            </label>
            <small>Supports JPG, PNG, PDF formats</small>
          </div>
        </div>

        {scans.length > 0 && (
          <div className="results">
            <h2>Scan Results</h2>
            {scans.map(scan => (
              <div key={scan.id} className="scan-card">
                <div className="scan-info">
                  <h4>{scan.filename}</h4>
                  <span className={`status ${scan.status.toLowerCase()}`}>
                    {scan.status}
                  </span>
                </div>
                {scan.status === 'COMPLETED' && (
                  <div className="scan-result">
                    <div className="score">Score: {scan.score}%</div>
                    <button 
                      onClick={() => exportScan(scan.id)}
                      className="export-btn"
                    >
                      Export Excel
                    </button>
                  </div>
                )}
                {scan.status === 'PROCESSING' && (
                  <div className="loading">Processing...</div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
