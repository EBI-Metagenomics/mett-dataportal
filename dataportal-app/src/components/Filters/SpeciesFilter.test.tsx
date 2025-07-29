import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import SpeciesFilter from './SpeciesFilter'

describe('SpeciesFilter', () => {
  const speciesList = [
    { acronym: 'BU', scientific_name: 'Bacteroides uniformis' },
    { acronym: 'PV', scientific_name: 'Parabacteroides vulgatus' },
  ]

  test('renders all species checkboxes', () => {
    render(
      <SpeciesFilter
        speciesList={speciesList}
        selectedSpecies={[]}
        onSpeciesSelect={() => {}}
      />
    )

    expect(screen.getByText('Bacteroides uniformis')).toBeInTheDocument()
    expect(screen.getByText('Parabacteroides vulgatus')).toBeInTheDocument()
    expect(screen.getAllByRole('checkbox')).toHaveLength(2)
  })

  test('checkboxes reflect selectedSpecies prop', () => {
    render(
      <SpeciesFilter
        speciesList={speciesList}
        selectedSpecies={['BU']}
        onSpeciesSelect={() => {}}
      />
    )

    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes[0]).toBeChecked()   // BU
    expect(checkboxes[1]).not.toBeChecked() // PV
  })

  test('calls onSpeciesSelect when checkbox is toggled', () => {
    const handleSelect = jest.fn()

    render(
      <SpeciesFilter
        speciesList={speciesList}
        selectedSpecies={[]}
        onSpeciesSelect={handleSelect}
      />
    )

    const checkbox = screen.getByLabelText(/Bacteroides uniformis/i)
    fireEvent.click(checkbox)
    expect(handleSelect).toHaveBeenCalledWith('BU')
  })
})
