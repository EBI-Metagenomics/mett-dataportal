import { URLSearchParams } from 'url';

export interface TabSelectionConfig {
  geneSearchParam: string;
  geneSortFieldParam: string;
  geneSortOrderParam: string;
  facetedFiltersParam: string;
  facetOperatorsParam: string;
  searchParam: string;
  sortFieldParam: string;
  sortOrderParam: string;
  tabParam: string;
}

export const DEFAULT_TAB_SELECTION_CONFIG: TabSelectionConfig = {
  geneSearchParam: 'geneSearch',
  geneSortFieldParam: 'geneSortField',
  geneSortOrderParam: 'geneSortOrder',
  facetedFiltersParam: 'facetedFilters',
  facetOperatorsParam: 'facetOperators',
  searchParam: 'search',
  sortFieldParam: 'sortField',
  sortOrderParam: 'sortOrder',
  tabParam: 'tab',
};

export const determineActiveTab = (
  searchParams: URLSearchParams,
  config: TabSelectionConfig = DEFAULT_TAB_SELECTION_CONFIG
): string => {
  // First check for explicit tab parameter
  const explicitTab = searchParams.get(config.tabParam);
  if (explicitTab && ['genomes', 'genes', 'proteinsearch'].includes(explicitTab)) {
    return explicitTab;
  }
  
  // Check for gene-specific parameters (more specific)
  const hasGeneSearch = searchParams.has(config.geneSearchParam);
  const hasGeneSort = searchParams.has(config.geneSortFieldParam) || searchParams.has(config.geneSortOrderParam);
  const hasFacetedFilters = searchParams.has(config.facetedFiltersParam) || searchParams.has(config.facetOperatorsParam);
  
  // Check for genome-specific parameters (more specific)
  const hasGenomeSearch = searchParams.has('genomeSearch'); // Use the new genome-specific param
  const hasGenomeSort = searchParams.has('genomeSortField') || searchParams.has('genomeSortOrder');
  
  // If gene-specific parameters are present, go to gene tab
  if (hasGeneSearch || hasGeneSort || hasFacetedFilters) {
    return 'genes'; // Gene Search tab
  }
  
  // If genome-specific parameters are present, go to genome tab
  if (hasGenomeSearch || hasGenomeSort) {
    return 'genomes'; // Genome Search tab
  }
  
  // Check for legacy parameters (fallback)
  const hasLegacySearch = searchParams.has(config.searchParam);
  const hasLegacySort = searchParams.has(config.sortFieldParam) || searchParams.has(config.sortOrderParam);
  
  if (hasLegacySearch || hasLegacySort) {
    // If it has faceted filters, it's likely gene-related
    if (hasFacetedFilters) {
      return 'genes'; // Gene Search tab
    }
    // Otherwise, assume genome-related
    return 'genomes'; // Genome Search tab
  }
  
  // Default to genome tab
  return 'genomes';
}; 