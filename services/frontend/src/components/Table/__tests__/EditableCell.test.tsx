import React from 'react'
import { render, fireEvent, waitFor } from '@testing-library/react'
import EditableCell from '../EditableCell'

describe('EditableCell', () => {
  it('renders value and enters edit mode on click', () => {
    const onSave = jest.fn()
    const { getByText, getByRole } = render(
      <EditableCell<string> value="Test" onSave={onSave} />
    )
    expect(getByText('Test')).toBeInTheDocument()
    fireEvent.click(getByText('Test'))
    expect(getByRole('textbox')).toBeInTheDocument()
  })

  it('validates input with validator', async () => {
    const onSave = jest.fn()
    const validator = (v: string) => v.length < 3 ? 'Too short' : null
    const { getByText, getByRole, findByText } = render(
      <EditableCell<string> value="abc" onSave={onSave} validator={validator} />
    )
    fireEvent.click(getByText('abc'))
    const input = getByRole('textbox')
    fireEvent.change(input, { target: { value: 'x' } })
    fireEvent.click(getByText('💾'))
    expect(await findByText('Too short')).toBeInTheDocument()
    expect(onSave).not.toHaveBeenCalled()
  })

  it('calls onSave and exits edit mode on valid save', async () => {
    const onSave = jest.fn().mockResolvedValue(undefined)
    const { getByText, getByRole, queryByRole } = render(
      <EditableCell<string> value="123" onSave={onSave} />
    )
    fireEvent.click(getByText('123'))
    const input = getByRole('textbox')
    fireEvent.change(input, { target: { value: '456' } })
    fireEvent.click(getByText('💾'))
    await waitFor(() => expect(onSave).toHaveBeenCalledWith('456'))
    expect(queryByRole('textbox')).toBeNull()
  })
})