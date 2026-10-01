import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import GeneSearchSidebar from './GeneSearchSidebar'

jest.mock('../../../../utils/common/constants', () => ({
  FACET_INITIAL_VISIBLE_CNT: 10,
  FACET_STEP_CNT: 10,
}))
jest.mock('@components/Filters/GeneFacetedFilter', () => () => <div>Gene facets</div>)

describe('GeneSearchSidebar', () => {
  test('shows shared Active filters panel for committed search on gene viewer', () => {
    render(
      <GeneSearchSidebar
        activeSearchLabel="PV_CCUG68662_01886"
        onClearSearch={jest.fn()}
        facets={{ total_hits: 0, operators: {} }}
        onToggleFacet={jest.fn()}
        hasActiveFacets={false}
      />
    )

    expect(screen.getByLabelText('Active filters')).toBeInTheDocument()
    expect(screen.getByText('Active filters (1)')).toBeInTheDocument()
    expect(screen.getByText('PV_CCUG68662_01886')).toBeInTheDocument()
    expect(screen.queryByText('Active Search')).not.toBeInTheDocument()
    expect(screen.queryByText(/Selected Genomes/i)).not.toBeInTheDocument()
  })

  test('hides Active filters chip when portaled into homepage rail', () => {
    render(
      <GeneSearchSidebar
        sidebarPortalId="homepage-gene-filters"
        activeSearchLabel="PV_CCUG68662_01886"
        onClearSearch={jest.fn()}
        facets={{ total_hits: 0, operators: {} }}
        onToggleFacet={jest.fn()}
        hasActiveFacets={false}
      />
    )

    expect(screen.queryByLabelText('Active filters')).not.toBeInTheDocument()
  })
})
