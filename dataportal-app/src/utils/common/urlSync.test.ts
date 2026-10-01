import { syncUrlToStore } from './urlSync'
import type { FilterState } from '../../stores/filterStore'

const createStore = (): FilterState => ({
  selectedSpecies: ['BU', 'ER'],
  selectedTypeStrains: ['BU_ATCC8492'],
  selectedGenomes: [{ isolate_name: 'BU_ATCC8492', type_strain: true } as FilterState['selectedGenomes'][number]],
  genomeSearchQuery: '',
  genomeSortField: 'species',
  genomeSortOrder: 'asc',
  geneSearchQuery: '',
  geneSortField: 'locus_tag',
  geneSortOrder: 'asc',
  facetedFilters: {},
  facetOperators: {},
  setSelectedSpecies: jest.fn(),
  setSelectedTypeStrains: jest.fn(),
  setSelectedGenomes: jest.fn(),
  setGenomeSearchQuery: jest.fn(),
  setGenomeSortField: jest.fn(),
  setGenomeSortOrder: jest.fn(),
  setGeneSearchQuery: jest.fn(),
  setGeneSortField: jest.fn(),
  setGeneSortOrder: jest.fn(),
  setFacetedFilters: jest.fn(),
  setFacetOperators: jest.fn(),
  addSelectedGenome: jest.fn(),
  removeSelectedGenome: jest.fn(),
  clearFacetedFilters: jest.fn(),
  resetFilters: jest.fn(),
} as unknown as FilterState)

describe('syncUrlToStore', () => {
  test('replaces species, type strains, and genomes when those params are absent', () => {
    const store = createStore()

    syncUrlToStore(new URLSearchParams('tab=genes'), store)

    expect(store.setSelectedSpecies).toHaveBeenCalledWith([])
    expect(store.setSelectedTypeStrains).toHaveBeenCalledWith([])
    expect(store.setSelectedGenomes).toHaveBeenCalledWith([])
  })

  test('loads only the species present in the query', () => {
    const store = createStore()

    syncUrlToStore(new URLSearchParams('species=BU&tab=genomes'), store)

    expect(store.setSelectedSpecies).toHaveBeenCalledWith(['BU'])
    expect(store.setSelectedTypeStrains).toHaveBeenCalledWith([])
    expect(store.setSelectedGenomes).toHaveBeenCalledWith([])
  })
})
