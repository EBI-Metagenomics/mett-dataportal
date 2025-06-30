import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { BaseGenome } from '../interfaces/Genome'

export interface FacetedFilters {
  essentiality?: string[];
  has_amr_info?: boolean[];
  pfam?: string[];
  interpro?: string[];
  kegg?: string[];
  cog_funcats?: string[];
  cog_id?: string[];
  go_term?: string[];
}

export interface FacetOperators {
  pfam?: 'AND' | 'OR';
  interpro?: 'AND' | 'OR';
  cog_id?: 'AND' | 'OR';
  cog_funcats?: 'AND' | 'OR';
  kegg?: 'AND' | 'OR';
  go_term?: 'AND' | 'OR';
}

export interface FilterState {
  selectedSpecies: string[]
  selectedTypeStrains: string[]
  selectedGenomes: BaseGenome[]
  genomeSearchQuery: string
  genomeSortField: string
  genomeSortOrder: 'asc' | 'desc'
  geneSearchQuery: string
  geneSortField: string
  geneSortOrder: 'asc' | 'desc'
  facetedFilters: FacetedFilters
  facetOperators: FacetOperators
  
  setSelectedSpecies: (species: string[]) => void
  setSelectedTypeStrains: (strains: string[]) => void
  setSelectedGenomes: (genomes: BaseGenome[]) => void
  addSelectedGenome: (genome: BaseGenome) => void
  removeSelectedGenome: (isolate_name: string) => void
  setGenomeSearchQuery: (query: string) => void
  setGenomeSortField: (field: string) => void
  setGenomeSortOrder: (order: 'asc' | 'desc') => void
  setGeneSearchQuery: (query: string) => void
  setGeneSortField: (field: string) => void
  setGeneSortOrder: (order: 'asc' | 'desc') => void
  setFacetedFilters: (filters: FacetedFilters) => void
  updateFacetedFilter: (filterType: keyof FacetedFilters, values: any[]) => void
  setFacetOperators: (operators: FacetOperators) => void
  updateFacetOperator: (filterType: keyof FacetOperators, operator: 'AND' | 'OR') => void
  resetFilters: () => void
}

const initialState = {
  selectedSpecies: [],
  selectedTypeStrains: [],
  selectedGenomes: [],
  genomeSearchQuery: '',
  genomeSortField: 'species',
  genomeSortOrder: 'asc' as const,
  geneSearchQuery: '',
  geneSortField: 'locus_tag',
  geneSortOrder: 'asc' as const,
  facetedFilters: {},
  facetOperators: {},
}

export const useFilterStore = create<FilterState>()(
  devtools(
    (set, get) => ({
      ...initialState,
      setSelectedSpecies: (species) => set({ selectedSpecies: species }),
      setSelectedTypeStrains: (strains) => set({ selectedTypeStrains: strains }),
      setSelectedGenomes: (genomes) => set({ selectedGenomes: genomes }),
      addSelectedGenome: (genome) => {
        const current = get().selectedGenomes;
        if (!current.some(g => g.isolate_name === genome.isolate_name)) {
          set({ selectedGenomes: [...current, genome] });
        }
      },
      removeSelectedGenome: (isolate_name) => {
        const current = get().selectedGenomes;
        set({ 
          selectedGenomes: current.filter(g => g.isolate_name !== isolate_name),
          selectedTypeStrains: get().selectedTypeStrains.filter(id => id !== isolate_name)
        });
      },
      setGenomeSearchQuery: (query) => set({ genomeSearchQuery: query }),
      setGenomeSortField: (field) => set({ genomeSortField: field }),
      setGenomeSortOrder: (order) => set({ genomeSortOrder: order }),
      setGeneSearchQuery: (query) => set({ geneSearchQuery: query }),
      setGeneSortField: (field) => set({ geneSortField: field }),
      setGeneSortOrder: (order) => set({ geneSortOrder: order }),
      setFacetedFilters: (filters) => set({ facetedFilters: filters }),
      updateFacetedFilter: (filterType, values) => {
        const current = get().facetedFilters;
        set({ 
          facetedFilters: {
            ...current,
            [filterType]: values.length > 0 ? values : undefined
          }
        });
      },
      setFacetOperators: (operators) => set({ facetOperators: operators }),
      updateFacetOperator: (filterType, operator) => {
        const current = get().facetOperators;
        set({ 
          facetOperators: {
            ...current,
            [filterType]: operator
          }
        });
      },
      resetFilters: () => set(initialState),
    }),
    { name: 'filter-store' }
  )
)
