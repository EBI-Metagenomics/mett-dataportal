import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import HomePageHeadBand from './HomePageHeadBand'
import { GenomeMeta } from '../../../interfaces/Genome'

jest.mock('../../../hooks/useFeatureFlags', () => ({
  useFeatureFlags: () => ({
    isFeatureEnabled: () => false,
  }),
}))

jest.mock('../../../utils/common/constants', () => ({
  EBI_FTP_SERVER: 'https://ftp.ebi.ac.uk/pub/databases/mett/',
}))

const typeStrains: GenomeMeta[] = [
  {
    species_scientific_name: 'Bacteroides uniformis',
    species_acronym: 'BU',
    isolate_name: 'BU_ATCC8492',
    assembly_name: 'BU_ATCC8492',
    fasta_file: '',
    gff_file: '',
    fasta_url: '',
    gff_url: '',
    type_strain: true,
    contigs: [],
  },
]

const speciesList = [
  { acronym: 'BU', scientific_name: 'Bacteroides uniformis', common_name: 'BU', taxonomy_id: 1 },
  { acronym: 'PV', scientific_name: 'Phocaeicola vulgatus', common_name: 'PV', taxonomy_id: 2 },
]

const renderHeadBand = (overrides: Partial<React.ComponentProps<typeof HomePageHeadBand>> = {}) =>
  render(
    <HomePageHeadBand
      typeStrains={typeStrains}
      linkTemplate="/genome/$strain_name"
      speciesList={speciesList}
      {...overrides}
    />
  )

describe('HomePageHeadBand', () => {
  test('renders browse type strains without a species section', () => {
    renderHeadBand()

    expect(screen.getByText('Browse type strains')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /BU_ATCC8492/i })).toBeInTheDocument()
    expect(screen.getByText('Bacteroides uniformis')).toBeInTheDocument()
    expect(screen.queryByText('Species')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /clear species filters/i })).not.toBeInTheDocument()
  })
})
