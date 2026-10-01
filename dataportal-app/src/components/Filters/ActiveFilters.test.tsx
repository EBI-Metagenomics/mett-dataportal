import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import ActiveFilters from './ActiveFilters'

describe('ActiveFilters', () => {
  test('renders chips with shared Active filters title', () => {
    const onClearAll = jest.fn()
    const onRemove = jest.fn()

    render(
      <ActiveFilters
        items={[{ id: 'search-1', label: 'PV_CCUG68662_01886', onRemove }]}
        onClearAll={onClearAll}
      />
    )

    expect(screen.getByLabelText('Active filters')).toBeInTheDocument()
    expect(screen.getByText('Active filters (1)')).toBeInTheDocument()
    expect(screen.getByText('PV_CCUG68662_01886')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /remove pv_ccug68662_01886/i }))
    expect(onRemove).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: /clear all/i }))
    expect(onClearAll).toHaveBeenCalledTimes(1)
  })

  test('returns null when there are no items', () => {
    const { container } = render(
      <ActiveFilters items={[]} onClearAll={jest.fn()} />
    )
    expect(container).toBeEmptyDOMElement()
  })
})
