import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import TypeStrainBrowse from './TypeStrainBrowse'
import { GenomeMeta } from '../../../interfaces/Genome'

const mockStrain = (isolate_name: string, species_acronym: string, scientific_name: string): GenomeMeta => ({
  species_scientific_name: scientific_name,
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

describe('TypeStrainBrowse', () => {
  const speciesList = [
    { acronym: 'BU', scientific_name: 'Bacteroides uniformis' },
    { acronym: 'PV', scientific_name: 'Phocaeicola vulgatus' },
  ]

  test('groups type strain links by species', () => {
    render(
      <TypeStrainBrowse
        typeStrains={[
          mockStrain('BU_ATCC8492', 'BU', 'Bacteroides uniformis'),
          mockStrain('PV_ATCC8482', 'PV', 'Phocaeicola vulgatus'),
          mockStrain('BU_3537', 'BU', 'Bacteroides uniformis'),
        ]}
        speciesList={speciesList}
        linkTemplate="/genome/$strain_name"
      />
    )

    expect(screen.getByText('Bacteroides uniformis')).toBeInTheDocument()
    expect(screen.getByText('Phocaeicola vulgatus')).toBeInTheDocument()

    const buLink = screen.getByRole('link', { name: /BU_ATCC8492/i })
    expect(buLink).toHaveAttribute('href', '/genome/BU_ATCC8492')
    expect(screen.getByRole('link', { name: /BU_3537/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /PV_ATCC8482/i })).toHaveAttribute('href', '/genome/PV_ATCC8482')
  })

  test('orders links by the type strain presentation sequence', () => {
    render(
      <TypeStrainBrowse
        typeStrains={[
          mockStrain('PV_ATCC8482', 'PV', 'Phocaeicola vulgatus'),
          mockStrain('BU_3537', 'BU', 'Bacteroides uniformis'),
          mockStrain('BU_ATCC8492', 'BU', 'Bacteroides uniformis'),
        ]}
        speciesList={speciesList}
        linkTemplate="/genome/$strain_name"
      />
    )

    const links = screen.getAllByRole('link').map((link) => link.textContent)
    expect(links[0]).toMatch(/BU_ATCC8492/)
    expect(links[1]).toMatch(/BU_3537/)
    expect(links[2]).toMatch(/PV_ATCC8482/)
  })

  test('shows a Show all toggle when there are more than 12 species groups', () => {
    const manySpecies = Array.from({ length: 13 }, (_, index) => ({
      acronym: `S${index}`,
      scientific_name: `Species ${index}`,
    }))
    const strains = manySpecies.map((species, index) =>
      mockStrain(`Z${String(index).padStart(2, '0')}_TYPE`, species.acronym, species.scientific_name)
    )

    render(
      <TypeStrainBrowse
        typeStrains={strains}
        speciesList={manySpecies}
        linkTemplate="/genome/$strain_name"
      />
    )

    expect(screen.getByText('Species 0')).toBeInTheDocument()
    expect(screen.queryByText('Species 12')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /show all type strains/i }))
    expect(screen.getByText('Species 12')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /show fewer type strains/i }))
    expect(screen.queryByText('Species 12')).not.toBeInTheDocument()
  })
})
