import React, { useState } from 'react'
import './EditableCell.css'

export interface EditableCellProps<T> {
  value: T
  onSave: (newValue: T) => Promise<void>
  validator?: (v: T) => string | null
}

function EditableCell<T extends string | number>({ value, onSave, validator }: EditableCellProps<T>) {
  const [editing, setEditing] = useState(false)
  const [current, setCurrent] = useState<T>(value)
  const [error, setError] = useState<string | null>(null)

  const startEdit = () => {
    setCurrent(value)
    setError(null)
    setEditing(true)
  }

  const cancelEdit = () => {
    setCurrent(value)
    setError(null)
    setEditing(false)
  }

  const saveEdit = async () => {
    if (validator) {
      const msg = validator(current)
      if (msg) {
        setError(msg)
        return
      }
    }
    try {
      await onSave(current)
      setEditing(false)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="editable-cell">
      {editing ? (
        <div className="edit-mode">
          <input
            className="edit-input"
            value={current}
            onChange={e => setCurrent((e.target.value as unknown) as T)}
          />
          <button className="btn-save" onClick={saveEdit}>💾</button>
          <button className="btn-cancel" onClick={cancelEdit}>✖️</button>
          {error && <div className="error-msg">{error}</div>}
        </div>
      ) : (
        <div className="view-mode" onClick={startEdit}>
          {value}
          <span className="edit-icon">✏️</span>
        </div>
      )}
    </div>
  )
}

export default EditableCell