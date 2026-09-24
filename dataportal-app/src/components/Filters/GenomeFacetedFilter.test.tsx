import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import GenomeFacetedFilter from './GenomeFacetedFilter'
import { GenomeMeta } from '../../interfaces/Genome'

const mockStrain = (isolate_name: string, species_acronym: string): GenomeMeta => ({
  species_scientific_name: species_acronym === 'BU' ? 'Bacteroides uniformis' : 'Phocaeicola vulgatus',
  species_acronym,
  isolate_name,
  assembly_name: isolate_name,
  fasta_file: '',
  gff_file: '',
  fasta_url: '',
  gff_url: '',
  type_strain: true,
  contigs: [],
})

const typeStrains: GenomeMeta[] = [
  mockStrain('BU_ATCC8492', 'BU'),
  mockStrain('BU_3537', 'BU'),
  mockStrain('PV_ATCC8482', 'PV'),
  mockStrain('PV_ET601', 'PV'),
]

describe('GenomeFacetedFilter', () => {
  test('renders filter header and type strain group', () => {
    render(
      <GenomeFacetedFilter
        typeStrains={typeStrains}
        selectedTypeStrains={[]}
        selectedSpecies={[]}
        onTypeStrainToggle={jest.fn()}
      />
    )

    expect(screen.getByText('Filter by Facets')).toBeInTheDocument()
    expect(screen.getByText(/TYPE STRAINS/i)).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /BU_ATCC8492/i })).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /PV_ATCC8482/i })).toBeInTheDocument()
  })

  test('collapses and expands the type strain group', () => {
    render(
      <GenomeFacetedFilter
        typeStrains={typeStrains}
        selectedTypeStrains={[]}
        selectedSpecies={[]}
        onTypeStrainToggle={jest.fn()}
      />
    )

    const heading = screen.getByText(/TYPE STRAINS/i)
    expect(screen.getByPlaceholderText(/filter the list/i)).toBeInTheDocument()

    fireEvent.click(heading)
    expect(screen.queryByPlaceholderText(/filter the list/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: /BU_ATCC8492/i })).not.toBeInTheDocument()

    fireEvent.click(heading)
    expect(screen.getByPlaceholderText(/filter the list/i)).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /BU_ATCC8492/i })).toBeInTheDocument()
  })

  test('filters the list based on search text', () => {
    render(
      <GenomeFacetedFilter
        typeStrains={typeStrains}
        selectedTypeStrains={[]}
        selectedSpecies={[]}
        onTypeStrainToggle={jest.fn()}
      />
    )

    fireEvent.change(screen.getByPlaceholderText(/filter the list/i), {
      target: { value: '3537' },
    })

    expect(screen.getByRole('checkbox', { name: /BU_3537/i })).toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: /BU_ATCC8492/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: /PV_ATCC8482/i })).not.toBeInTheDocument()
  })

  test('hides type strains that do not match selected species', () => {
    render(
      <GenomeFacetedFilter
        typeStrains={typeStrains}
        selectedTypeStrains={[]}
        selectedSpecies={['BU']}
        onTypeStrainToggle={jest.fn()}
      />
    )

    expect(screen.getByRole('checkbox', { name: /BU_ATCC8492/i })).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /BU_3537/i })).toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: /PV_ATCC8482/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: /PV_ET601/i })).not.toBeInTheDocument()
  })

  test('keeps selected type strains visible when species gating would hide them', () => {
    render(
      <GenomeFacetedFilter
        typeStrains={typeStrains}
        selectedTypeStrains={['PV_ATCC8482']}
        selectedSpecies={['BU']}
        onTypeStrainToggle={jest.fn()}
      />
    )

    const selected = screen.getByRole('checkbox', { name: /PV_ATCC8482/i })
    expect(selected).toBeChecked()
    expect(selected).toBeDisabled()
    expect(screen.getByRole('checkbox', { name: /BU_ATCC8492/i })).toBeInTheDocument()
  })

  test('calls onToggle when an enabled checkbox is clicked', () => {
    const onToggle = jest.fn()
    render(
      <GenomeFacetedFilter
        typeStrains={typeStrains}
        selectedTypeStrains={[]}
        selectedSpecies={[]}
        onTypeStrainToggle={onToggle}
      />
    )

    fireEvent.click(screen.getByRole('checkbox', { name: /BU_ATCC8492/i }))
    expect(onToggle).toHaveBeenCalledWith('BU_ATCC8492')
  })

  test('calls onClearAll when Clear all is clicked', () => {
    const onClearAll = jest.fn()
    render(
      <GenomeFacetedFilter
        typeStrains={typeStrains}
        selectedTypeStrains={['BU_ATCC8492', 'PV_ATCC8482']}
        selectedSpecies={[]}
        onTypeStrainToggle={jest.fn()}
        onClearAll={onClearAll}
      />
    )

    const clearButton = screen.getByRole('button', { name: /clear all facet filters/i })
    expect(clearButton).toHaveTextContent('Clear all (2)')
    fireEvent.click(clearButton)
    expect(onClearAll).toHaveBeenCalledTimes(1)
  })
})
