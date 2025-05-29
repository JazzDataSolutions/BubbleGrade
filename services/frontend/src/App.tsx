import { useState, useCallback, useEffect } from 'react'
import './App.css'
import UploadCard from './components/Upload/UploadCard'
import EditableCell from './components/Table/EditableCell'
import ProgressDrawer from './components/ProgressDrawer/ProgressDrawer'
import { apiService } from './services/api'

interface ScanResult {
  id: string
  filename: string
  status: string
  nombre: { value: string }
  curp: { value: string }
  score?: number
}

function App() {
  const [scans, setScans] = useState<ScanResult[]>([])
  const [progressVisible, setProgressVisible] = useState(false)
  const [currentScanId, setCurrentScanId] = useState('')

  const loadScans = useCallback(async () => {
    try {
      const res = await apiService.getScans()
      setScans(res.scans)
    } catch (e) {
      console.error('Failed to load scans', e)
    }
  }, [])

  useEffect(() => { loadScans() }, [loadScans])

  const handleFiles = useCallback(async (files: File[]) => {
    for (const file of files) {
      try {
        const result = await apiService.uploadScan(file)
        setCurrentScanId(result.id)
        setProgressVisible(true)
      } catch (e) {
        console.error('Upload error', e)
      }
    }
    loadScans()
  }, [loadScans])

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
        <UploadCard onFiles={handleFiles} />
        <ProgressDrawer
          visible={progressVisible}
          onClose={() => setProgressVisible(false)}
          scanId={currentScanId}
        />

        <section className="results">
          <h2>Scan Results</h2>
          <table>
            <thead>
              <tr>
                <th>Filename</th>
                <th>Status</th>
                <th>Nombre</th>
                <th>CURP</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {scans.map(scan => (
                <tr key={scan.id}>
                  <td>{scan.filename}</td>
                  <td>{scan.status}</td>
                  <td>
                    <EditableCell<string>
                      value={scan.nombre.value}
                      onSave={async v => { await apiService.updateScan(scan.id, { nombre: { value: v } }); loadScans() }}
                    />
                  </td>
                  <td>
                    <EditableCell<string>
                      value={scan.curp.value}
                      validator={v => {
                        const curpRegex = /^[A-Z]{4}\d{6}[HM][A-Z]{5}\d{2}$/
                        return curpRegex.test(v)
                          ? null
                          : 'Formato CURP inválido'
                      }}
                      onSave={async v => {
                        await apiService.updateScan(scan.id, { curp: { value: v } })
                        loadScans()
                      }}
                    />
                  </td>
                  <td>{scan.score ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  )
}

export default App
