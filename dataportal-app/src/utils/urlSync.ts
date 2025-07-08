import { useFilterStore, FilterState } from '../stores/filterStore';

export interface UrlSyncConfig {
  // URL parameter names
  speciesParam: string;
  typeStrainsParam: string;
  selectedGenomesParam: string;
  searchParam: string;
  sortFieldParam: string;
  sortOrderParam: string;
  geneSearchParam: string;
  geneSortFieldParam: string;
  geneSortOrderParam: string;
  facetedFiltersParam: string;
  facetOperatorsParam: string;
  
  // Default values
  defaultSortField: string;
  defaultSortOrder: 'asc' | 'desc';
}

export const DEFAULT_URL_SYNC_CONFIG: UrlSyncConfig = {
  speciesParam: 'species',
  typeStrainsParam: 'typeStrains',
  selectedGenomesParam: 'selectedGenomes',
  searchParam: 'search',
  sortFieldParam: 'sortField',
  sortOrderParam: 'sortOrder',
  geneSearchParam: 'geneSearch',
  geneSortFieldParam: 'geneSortField',
  geneSortOrderParam: 'geneSortOrder',
  facetedFiltersParam: 'facetedFilters',
  facetOperatorsParam: 'facetOperators',
  defaultSortField: 'species',
  defaultSortOrder: 'asc',
};

// Separate configs for each tab to avoid conflicts
export const GENOME_TAB_URL_CONFIG: UrlSyncConfig = {
  speciesParam: 'species',
  typeStrainsParam: 'typeStrains',
  selectedGenomesParam: 'selectedGenomes',
  searchParam: 'genomeSearch',
  sortFieldParam: 'genomeSortField',
  sortOrderParam: 'genomeSortOrder',
  geneSearchParam: 'geneSearch',
  geneSortFieldParam: 'geneSortField',
  geneSortOrderParam: 'geneSortOrder',
  facetedFiltersParam: 'facetedFilters',
  facetOperatorsParam: 'facetOperators',
  defaultSortField: 'species',
  defaultSortOrder: 'asc',
};

export const GENE_TAB_URL_CONFIG: UrlSyncConfig = {
  speciesParam: 'species',
  typeStrainsParam: 'typeStrains',
  selectedGenomesParam: 'selectedGenomes',
  searchParam: 'search',
  sortFieldParam: 'sortField',
  sortOrderParam: 'sortOrder',
  geneSearchParam: 'geneSearch',
  geneSortFieldParam: 'geneSortField',
  geneSortOrderParam: 'geneSortOrder',
  facetedFiltersParam: 'facetedFilters',
  facetOperatorsParam: 'facetOperators',
  defaultSortField: 'locus_tag',
  defaultSortOrder: 'asc',
};

export const syncUrlToStore = (
  searchParams: URLSearchParams,
  filterStore: FilterState,
  config: UrlSyncConfig = DEFAULT_URL_SYNC_CONFIG
): void => {
  // Sync species
  const species = searchParams.getAll(config.speciesParam);
  if (species.length > 0) {
    filterStore.setSelectedSpecies(species);
  }

  // Sync type strains
  const typeStrains = searchParams.getAll(config.typeStrainsParam);
  if (typeStrains.length > 0) {
    filterStore.setSelectedTypeStrains(typeStrains);
  }

  // Sync selected genomes (as isolate names)
  const selectedGenomes = searchParams.getAll(config.selectedGenomesParam);
  if (selectedGenomes.length > 0) {
    // Convert isolate names back to genome objects
    const genomeObjects = selectedGenomes.map(isolate_name => ({
      isolate_name,
      type_strain: false, // Default value, will be updated when actual data is loaded
    }));
    filterStore.setSelectedGenomes(genomeObjects);
  }

  // Sync genome search query
  const searchQuery = searchParams.get(config.searchParam);
  if (searchQuery) {
    filterStore.setGenomeSearchQuery(searchQuery);
  }

  // Sync genome sort field
  const sortField = searchParams.get(config.sortFieldParam);
  if (sortField) {
    filterStore.setGenomeSortField(sortField);
  }

  // Sync genome sort order
  const sortOrder = searchParams.get(config.sortOrderParam) as 'asc' | 'desc';
  if (sortOrder && (sortOrder === 'asc' || sortOrder === 'desc')) {
    filterStore.setGenomeSortOrder(sortOrder);
  }

  // Sync gene search query
  const geneSearchQuery = searchParams.get(config.geneSearchParam);
  if (geneSearchQuery) {
    filterStore.setGeneSearchQuery(geneSearchQuery);
  }

  // Sync gene sort field
  const geneSortField = searchParams.get(config.geneSortFieldParam);
  if (geneSortField) {
    filterStore.setGeneSortField(geneSortField);
  }

  // Sync gene sort order
  const geneSortOrder = searchParams.get(config.geneSortOrderParam) as 'asc' | 'desc';
  if (geneSortOrder && (geneSortOrder === 'asc' || geneSortOrder === 'desc')) {
    filterStore.setGeneSortOrder(geneSortOrder);
  }

  // Sync faceted filters
  const facetedFiltersStr = searchParams.get(config.facetedFiltersParam);
  if (facetedFiltersStr) {
    try {
      const facetedFilters = JSON.parse(decodeURIComponent(facetedFiltersStr));
      filterStore.setFacetedFilters(facetedFilters);
    } catch (error) {
      console.error('Error parsing faceted filters from URL:', error);
    }
  }

  // Sync facet operators
  const facetOperatorsStr = searchParams.get(config.facetOperatorsParam);
  if (facetOperatorsStr) {
    try {
      const facetOperators = JSON.parse(decodeURIComponent(facetOperatorsStr));
      filterStore.setFacetOperators(facetOperators);
    } catch (error) {
      console.error('Error parsing facet operators from URL:', error);
    }
  }
};

export const syncStoreToUrl = (
  filterStore: FilterState,
  config: UrlSyncConfig = DEFAULT_URL_SYNC_CONFIG
): Record<string, string | string[] | null> => {
  return {
    [config.speciesParam]: filterStore.selectedSpecies.length > 0 ? filterStore.selectedSpecies : null,
    [config.typeStrainsParam]: filterStore.selectedTypeStrains.length > 0 ? filterStore.selectedTypeStrains : null,
    [config.selectedGenomesParam]: filterStore.selectedGenomes.length > 0 ? filterStore.selectedGenomes.map(g => g.isolate_name) : null,
    [config.searchParam]: filterStore.genomeSearchQuery || null,
    [config.sortFieldParam]: filterStore.genomeSortField,
    [config.sortOrderParam]: filterStore.genomeSortOrder,
    [config.geneSearchParam]: filterStore.geneSearchQuery || null,
    [config.geneSortFieldParam]: filterStore.geneSortField,
    [config.geneSortOrderParam]: filterStore.geneSortOrder,
    [config.facetedFiltersParam]: Object.keys(filterStore.facetedFilters).length > 0 ? encodeURIComponent(JSON.stringify(filterStore.facetedFilters)) : null,
    [config.facetOperatorsParam]: Object.keys(filterStore.facetOperators).length > 0 ? encodeURIComponent(JSON.stringify(filterStore.facetOperators)) : null,
  };
};

export const buildShareableUrl = (
  baseUrl: string,
  filters: Record<string, any>,
  config: UrlSyncConfig = DEFAULT_URL_SYNC_CONFIG
): string => {
  const url = new URL(baseUrl, window.location.origin);
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') {
      return;
    }
    
    if (Array.isArray(value)) {
      if (value.length > 0) {
        value.forEach(v => url.searchParams.append(key, v));
      }
    } else {
      url.searchParams.set(key, String(value));
    }
  });
  
  return url.toString();
};

export const parseUrlFilters = (searchParams: URLSearchParams): Record<string, string | string[]> => {
  const filters: Record<string, string | string[]> = {};
  
  for (const [key, value] of searchParams.entries()) {
    if (filters[key]) {
      if (Array.isArray(filters[key])) {
        (filters[key] as string[]).push(value);
      } else {
        filters[key] = [filters[key] as string, value];
      }
    } else {
      filters[key] = value;
    }
  }
  
  return filters;
}; 