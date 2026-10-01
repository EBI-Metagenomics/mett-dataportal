import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import GeneSearchSidebar from './GeneSearchSidebar'

jest.mock('../../../../utils/common/constants', () => ({
  FACET_INITIAL_VISIBLE_CNT: 10,
  FACET_STEP_CNT: 10,
}))
jest.mock('@components/Filters/GeneFacetedFilter', () => () => <div>Gene facets</div>)

const mockFacetedFilters = jest.fn()
jest.mock('../../../../stores/filterStore', () => ({
  useFilterStore: (selector?: (state: any) => unknown) => {
    const state = {
      facetedFilters: mockFacetedFilters(),
    }
    return selector ? selector(state) : state
  },
}))

describe('GeneSearchSidebar', () => {
  beforeEach(() => {
    mockFacetedFilters.mockReturnValue({})
  })

  test('shows shared Active filters panel for search and facet chips on gene viewer', () => {
    mockFacetedFilters.mockReturnValue({
      has_amr_info: [true],
      interpro: ['IPR000531'],
    })
    const onClearSearch = jest.fn()
    const onToggleFacet = jest.fn()
    const onClearAllFacets = jest.fn()

    render(
      <GeneSearchSidebar
        activeSearchLabel="PV_CCUG68662_01886"
        onClearSearch={onClearSearch}
        facets={{ total_hits: 0, operators: {} }}
        onToggleFacet={onToggleFacet}
        hasActiveFacets
        onClearAllFacets={onClearAllFacets}
      />
    )

    expect(screen.getByLabelText('Active filters')).toBeInTheDocument()
    expect(screen.getByText('Active filters (3)')).toBeInTheDocument()
    expect(screen.getByText('PV_CCUG68662_01886')).toBeInTheDocument()
    expect(screen.getByText('AMR: Present')).toBeInTheDocument()
    expect(screen.getByText('InterPro: IPR000531')).toBeInTheDocument()
    expect(screen.queryByText('Filter by Facets')).not.toBeInTheDocument()
    expect(screen.queryByText('Active Search')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /clear all/i }))
    expect(onClearSearch).toHaveBeenCalledTimes(1)
    expect(onClearAllFacets).toHaveBeenCalledTimes(1)
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
