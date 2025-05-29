import React from 'react'
import { render, act } from '@testing-library/react'
import ProgressDrawer from '../ProgressDrawer'

describe('ProgressDrawer', () => {
  let originalWebSocket: any
  let mockInstance: any

  beforeAll(() => {
    originalWebSocket = (global as any).WebSocket
    mockInstance = { onopen: null, onmessage: null, onerror: null, close: jest.fn() }
    (global as any).WebSocket = jest.fn(() => mockInstance)
  })

  afterAll(() => {
    (global as any).WebSocket = originalWebSocket
  })

  it('renders messages received via WebSocket', async () => {
    const { getByText, queryByText, rerender } = render(
      <ProgressDrawer visible={true} onClose={() => {}} scanId="scan1" />
    )
    // Initially no messages
    expect(queryByText('message1')).toBeNull()
    // Simulate WebSocket open
    act(() => {
      mockInstance.onopen()
    })
    // Simulate receiving a message for a different scan
    act(() => {
      mockInstance.onmessage({ data: JSON.stringify({ scan_id: 'other', stage: 'message1' }) })
    })
    expect(queryByText('message1')).toBeNull()
    // Simulate receiving a message for the correct scan
    act(() => {
      mockInstance.onmessage({ data: JSON.stringify({ scan_id: 'scan1', stage: 'step1' }) })
    })
    expect(getByText('step1')).toBeInTheDocument()
  })
})