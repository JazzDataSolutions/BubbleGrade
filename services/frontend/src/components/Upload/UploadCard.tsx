import React, { useState, useRef } from 'react'
import './UploadCard.css'

export interface UploadCardProps {
  onFiles: (files: File[]) => void
  accept?: string
  maxSizeMB?: number
}

const UploadCard: React.FC<UploadCardProps> = ({
  onFiles,
  accept = 'image/*,.pdf',
  maxSizeMB = 10
}) => {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateAndSend = (files: FileList | File[]) => {
    const arr = Array.from(files)
    const invalid = arr.find(f => f.size > maxSizeMB * 1024 * 1024)
    if (invalid) {
      setError(`El archivo ${invalid.name} excede ${maxSizeMB} MB`)
      return
    }
    setError(null)
    onFiles(arr)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    validateAndSend(e.dataTransfer.files)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  const handleFilesSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      validateAndSend(e.target.files)
    }
  }

  return (
    <div
      className={`upload-card ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
      onClick={handleButtonClick}
      onKeyPress={e => { if (e.key === 'Enter') handleButtonClick() }}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={accept}
        style={{ display: 'none' }}
        onChange={handleFilesSelected}
      />
      <div className="icon">📄</div>
      <p>Arrastra y suelta tu hoja aquí</p>
      <button type="button" className="btn-secondary">Seleccionar Archivos</button>
      {error && <div className="error">{error}</div>}
      <small>Formatos: JPG, PNG, PDF (≤ {maxSizeMB} MB)</small>
    </div>
  )
}

export default UploadCard