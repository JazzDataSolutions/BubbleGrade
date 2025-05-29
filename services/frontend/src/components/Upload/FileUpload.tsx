import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useAppStore } from '../../store'
import { apiService } from '../../services/api'
import './FileUpload.css'

interface FileUploadProps {
  onUploadComplete?: (scanId: string) => void
  maxFiles?: number
  maxSize?: number // in MB
}

interface UploadProgress {
  file: File
  progress: number
  status: 'uploading' | 'success' | 'error'
  scanId?: string
  error?: string
}

const ACCEPTED_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/tiff': ['.tiff', '.tif'],
  'application/pdf': ['.pdf']
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

export const FileUpload: React.FC<FileUploadProps> = ({ 
  onUploadComplete, 
  maxFiles = 5,
  maxSize = 10 
}) => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([])
  const { addScan, setIsUploading, addNotification, activeTemplate } = useAppStore()

  const validateFile = useCallback((file: File): string | null => {
    if (file.size > maxSize * 1024 * 1024) {
      return `File too large. Maximum size is ${maxSize}MB`
    }

    const isValidType = Object.keys(ACCEPTED_TYPES).includes(file.type)
    if (!isValidType) {
      return 'Invalid file type. Please upload JPG, PNG, TIFF, or PDF files'
    }

    return null
  }, [maxSize])

  const uploadFile = useCallback(async (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      addNotification({
        type: 'error',
        title: 'Invalid File',
        message: validationError
      })
      return
    }

    const progressId = crypto.randomUUID()
    
    setUploadProgress(prev => [...prev, {
      file,
      progress: 0,
      status: 'uploading'
    }])

    try {
      setIsUploading(true)

      const result = await apiService.uploadScan(file, {
        templateId: activeTemplate?.id,
        onProgress: (progress: number) => {
          setUploadProgress(prev => 
            prev.map(item => 
              item.file === file 
                ? { ...item, progress }
                : item
            )
          )
        }
      })

      // Update progress to success
      setUploadProgress(prev => 
        prev.map(item => 
          item.file === file 
            ? { ...item, status: 'success', scanId: result.id, progress: 100 }
            : item
        )
      )

      // Add to global state
      addScan({
        id: result.id,
        filename: file.name,
        status: result.status,
        uploadTime: new Date().toISOString()
      })

      addNotification({
        type: 'success',
        title: 'Upload Successful',
        message: `${file.name} uploaded and queued for processing`
      })

      onUploadComplete?.(result.id)

    } catch (error) {
      setUploadProgress(prev => 
        prev.map(item => 
          item.file === file 
            ? { 
                ...item, 
                status: 'error', 
                error: error instanceof Error ? error.message : 'Upload failed'
              }
            : item
        )
      )

      addNotification({
        type: 'error',
        title: 'Upload Failed',
        message: `Failed to upload ${file.name}`
      })
    } finally {
      setIsUploading(false)
      
      // Clear progress after 3 seconds
      setTimeout(() => {
        setUploadProgress(prev => 
          prev.filter(item => item.file !== file)
        )
      }, 3000)
    }
  }, [validateFile, addScan, setIsUploading, addNotification, activeTemplate, onUploadComplete])

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    rejectedFiles.forEach(({ file, errors }) => {
      const errorMessage = errors.map((e: any) => e.message).join(', ')
      addNotification({
        type: 'error',
        title: 'File Rejected',
        message: `${file.name}: ${errorMessage}`
      })
    })

    // Upload accepted files
    acceptedFiles.forEach(uploadFile)
  }, [uploadFile, addNotification])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles,
    maxSize: MAX_FILE_SIZE,
    multiple: true
  })

  const clearProgress = useCallback(() => {
    setUploadProgress([])
  }, [])

  return (
    <div className="file-upload">
      <div 
        {...getRootProps()} 
        className={`upload-zone ${isDragActive ? 'drag-active' : ''} ${isDragReject ? 'drag-reject' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="upload-content">
          <div className="upload-icon">
            {isDragActive ? '📥' : '📄'}
          </div>
          <h3>
            {isDragActive 
              ? 'Drop files here' 
              : 'Upload bubble sheets'
            }
          </h3>
          <p>
            Drag & drop files here, or click to select
          </p>
          <div className="upload-info">
            <span>Supports: JPG, PNG, TIFF, PDF</span>
            <span>Max size: {maxSize}MB per file</span>
            <span>Max files: {maxFiles}</span>
          </div>
          {activeTemplate && (
            <div className="template-info">
              📋 Using template: <strong>{activeTemplate.name}</strong>
            </div>
          )}
        </div>
      </div>

      {uploadProgress.length > 0 && (
        <div className="upload-progress">
          <div className="progress-header">
            <h4>Upload Progress</h4>
            <button onClick={clearProgress} className="clear-btn">
              Clear
            </button>
          </div>
          {uploadProgress.map((item, index) => (
            <div key={index} className="progress-item">
              <div className="progress-info">
                <span className="filename">{item.file.name}</span>
                <span className={`status ${item.status}`}>
                  {item.status === 'uploading' && `${item.progress}%`}
                  {item.status === 'success' && '✅'}
                  {item.status === 'error' && '❌'}
                </span>
              </div>
              {item.status === 'uploading' && (
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              )}
              {item.error && (
                <div className="error-message">{item.error}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}