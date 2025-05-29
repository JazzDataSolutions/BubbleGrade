import React, { useState, useCallback } from 'react'
import { ProcessedScan, CURPValidation, EditSession } from '../../types/snapgrade'
import { validateCURP } from '../../utils/curpValidator'
import { useDebouncedCallback } from '../../hooks/useDebounce'
import './NameCURPEditor.css'

interface NameCURPEditorProps {
  scan: ProcessedScan
  onSave: (updates: Partial<ProcessedScan>) => Promise<void>
  onCancel: () => void
  imagePreviewUrl?: string
}

export const NameCURPEditor: React.FC<NameCURPEditorProps> = ({
  scan,
  onSave,
  onCancel,
  imagePreviewUrl
}) => {
  const [editSession, setEditSession] = useState<EditSession>({
    scanId: scan.id,
    originalData: scan,
    currentData: { ...scan },
    hasChanges: false,
    validationErrors: []
  })

  const [isValidating, setIsValidating] = useState(false)
  const [curpValidation, setCurpValidation] = useState<CURPValidation | null>(null)

  // Debounced CURP validation
  const debouncedValidateCURP = useDebouncedCallback(
    async (curp: string) => {
      if (curp.length >= 10) {
        setIsValidating(true)
        try {
          const validation = await validateCURP(curp)
          setCurpValidation(validation)
          
          // Update validation errors
          setEditSession(prev => ({
            ...prev,
            validationErrors: prev.validationErrors.filter(e => e.field !== 'curp').concat(
              !validation.isValid ? [{
                field: 'curp' as const,
                message: 'CURP inválido - revisar formato y dígito verificador',
                severity: 'error' as const
              }] : []
            )
          }))
        } catch (error) {
          console.error('Error validating CURP:', error)
        } finally {
          setIsValidating(false)
        }
      }
    },
    500
  )

  const updateField = useCallback((
    field: 'nombre' | 'curp',
    value: string
  ) => {
    setEditSession(prev => {
      const updated = {
        ...prev,
        currentData: {
          ...prev.currentData,
          [field]: {
            ...prev.currentData[field],
            value: value.toUpperCase(),
            needsReview: false,
            correctedBy: 'user', // Would be actual user ID
            correctedAt: new Date().toISOString()
          }
        },
        hasChanges: true
      }

      // Trigger CURP validation
      if (field === 'curp') {
        debouncedValidateCURP(value)
      }

      return updated
    })
  }, [debouncedValidateCURP])

  const handleSave = useCallback(async () => {
    // Validate before saving
    const errors = []
    
    if (!editSession.currentData.nombre.value.trim()) {
      errors.push({
        field: 'nombre' as const,
        message: 'Nombre es requerido',
        severity: 'error' as const
      })
    }

    if (!editSession.currentData.curp.value.trim()) {
      errors.push({
        field: 'curp' as const,
        message: 'CURP es requerido',
        severity: 'error' as const
      })
    }

    if (curpValidation && !curpValidation.isValid) {
      errors.push({
        field: 'curp' as const,
        message: 'CURP debe ser válido',
        severity: 'error' as const
      })
    }

    if (errors.length > 0) {
      setEditSession(prev => ({ ...prev, validationErrors: errors }))
      return
    }

    try {
      await onSave({
        nombre: editSession.currentData.nombre,
        curp: editSession.currentData.curp,
        status: 'COMPLETED'
      })
    } catch (error) {
      console.error('Error saving changes:', error)
    }
  }, [editSession, curpValidation, onSave])

  const confidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'confidence-high'
    if (confidence >= 0.7) return 'confidence-medium'
    return 'confidence-low'
  }

  return (
    <div className="name-curp-editor">
      <div className="editor-header">
        <h3>Editar Datos OCR</h3>
        <div className="editor-actions">
          <button 
            onClick={onCancel} 
            className="btn-secondary"
          >
            Cancelar
          </button>
          <button 
            onClick={handleSave}
            disabled={!editSession.hasChanges || editSession.validationErrors.some(e => e.severity === 'error')}
            className="btn-primary"
          >
            Guardar Cambios
          </button>
        </div>
      </div>

      <div className="editor-content">
        {/* Image Preview with Regions */}
        {imagePreviewUrl && (
          <div className="image-preview">
            <img src={imagePreviewUrl} alt="Scan preview" />
            <div 
              className="region-overlay region-nombre"
              style={{
                left: `${scan.regions.nombre.x}%`,
                top: `${scan.regions.nombre.y}%`,
                width: `${scan.regions.nombre.width}%`,
                height: `${scan.regions.nombre.height}%`
              }}
            >
              NOMBRE
            </div>
            <div 
              className="region-overlay region-curp"
              style={{
                left: `${scan.regions.curp.x}%`,
                top: `${scan.regions.curp.y}%`,
                width: `${scan.regions.curp.width}%`,
                height: `${scan.regions.curp.height}%`
              }}
            >
              CURP
            </div>
          </div>
        )}

        {/* Edit Fields */}
        <div className="edit-fields">
          <div className="field-group">
            <label className="field-label">
              Nombre Completo
              <span className={`confidence-badge ${confidenceColor(scan.nombre.confidence)}`}>
                {Math.round(scan.nombre.confidence * 100)}% confianza
              </span>
            </label>
            <input
              type="text"
              value={editSession.currentData.nombre.value}
              onChange={(e) => updateField('nombre', e.target.value)}
              className="field-input"
              placeholder="NOMBRE COMPLETO DEL ALUMNO"
              maxLength={100}
            />
            <div className="field-hint">
              Original OCR: "{scan.nombre.value}"
            </div>
          </div>

          <div className="field-group">
            <label className="field-label">
              CURP
              <span className={`confidence-badge ${confidenceColor(scan.curp.confidence)}`}>
                {Math.round(scan.curp.confidence * 100)}% confianza
              </span>
              {isValidating && <span className="validating">Validando...</span>}
            </label>
            <input
              type="text"
              value={editSession.currentData.curp.value}
              onChange={(e) => updateField('curp', e.target.value)}
              className="field-input curp-input"
              placeholder="AAAA######HAAAAA##"
              maxLength={18}
              style={{ fontFamily: 'monospace' }}
            />
            <div className="field-hint">
              Original OCR: "{scan.curp.value}"
            </div>
            
            {/* CURP Validation Display */}
            {curpValidation && (
              <div className={`curp-validation ${curpValidation.isValid ? 'valid' : 'invalid'}`}>
                <div className="validation-status">
                  {curpValidation.isValid ? '✅ CURP Válido' : '❌ CURP Inválido'}
                </div>
                {curpValidation.federalEntity && (
                  <div className="curp-details">
                    Estado: {curpValidation.federalEntity} | 
                    Fecha: {curpValidation.birthDate} | 
                    Sexo: {curpValidation.gender}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Validation Errors */}
        {editSession.validationErrors.length > 0 && (
          <div className="validation-errors">
            {editSession.validationErrors.map((error, index) => (
              <div key={index} className={`error ${error.severity}`}>
                <strong>{error.field.toUpperCase()}:</strong> {error.message}
              </div>
            ))}
          </div>
        )}

        {/* Processing Quality Metrics */}
        <div className="quality-metrics">
          <h4>Métricas de Calidad</h4>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-label">Resolución:</span>
              <span className="metric-value">
                {scan.imageQuality.resolution.width}x{scan.imageQuality.resolution.height}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Claridad:</span>
              <span className="metric-value">
                {Math.round(scan.imageQuality.clarity * 100)}%
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Inclinación:</span>
              <span className="metric-value">
                {scan.imageQuality.skew.toFixed(1)}°
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}