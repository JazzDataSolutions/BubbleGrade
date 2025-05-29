// Enhanced types for SnapGrade with OCR capabilities

export interface ProcessedScan {
  id: string
  filename: string
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'ERROR' | 'NEEDS_REVIEW'
  
  // OCR Results
  nombre: {
    value: string
    confidence: number
    needsReview: boolean
    correctedBy?: string
    correctedAt?: string
  }
  
  curp: {
    value: string
    confidence: number
    isValid: boolean
    needsReview: boolean
    correctedBy?: string
    correctedAt?: string
  }
  
  // OMR Results (existing)
  score?: number
  answers?: string[]
  totalQuestions?: number
  
  // Processing metadata
  uploadTime: string
  processedTime?: string
  reviewTime?: string
  
  // Quality metrics
  imageQuality: {
    resolution: { width: number; height: number }
    clarity: number
    skew: number
  }
  
  // Regional bounding boxes for editing UI
  regions: {
    nombre: BoundingBox
    curp: BoundingBox
    omr: BoundingBox
  }
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface CURPValidation {
  isValid: boolean
  format: boolean
  checksum: boolean
  federalEntity: string | null
  birthDate: string | null
  gender: 'M' | 'F' | null
}

export interface EditSession {
  scanId: string
  originalData: ProcessedScan
  currentData: ProcessedScan
  hasChanges: boolean
  validationErrors: ValidationError[]
}

export interface ValidationError {
  field: 'nombre' | 'curp'
  message: string
  severity: 'error' | 'warning'
}