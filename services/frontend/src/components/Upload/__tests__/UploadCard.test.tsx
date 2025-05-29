import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import UploadCard from '../UploadCard'

describe('UploadCard', () => {
  it('calls onFiles when files are selected via input', () => {
    const onFiles = jest.fn()
    const { getByRole } = render(<UploadCard onFiles={onFiles} />)
    const input = getByRole('button').querySelector('input[type="file"]')!
    const file = new File(['hello'], 'hello.png', { type: 'image/png' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(onFiles).toHaveBeenCalledWith([file])
  })

  it('rejects files larger than maxSizeMB', () => {
    const onFiles = jest.fn()
    const { getByText, getByRole } = render(<UploadCard onFiles={onFiles} maxSizeMB={0.00001} />)
    const input = getByRole('button').querySelector('input[type="file"]')!
    const largeFile = new File(['a'.repeat(1024 * 1024)], 'big.png', { type: 'image/png' })
    fireEvent.change(input, { target: { files: [largeFile] } })
    expect(getByText(/excede/)).toBeInTheDocument()
    expect(onFiles).not.toHaveBeenCalled()
  })
})