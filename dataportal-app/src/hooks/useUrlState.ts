import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

interface UrlState {
  query?: string;
  page?: number;
  pageSize?: number;
  sortField?: string;
  sortOrder?: 'asc' | 'desc';
  selectedSpecies?: string[];
  selectedTypeStrains?: string[];
  selectedFacets?: Record<string, string[]>;
  facetOperators?: Record<string, 'AND' | 'OR'>;
}

// Default facet operator is OR
const DEFAULT_FACET_OPERATOR = 'OR' as const;

export const useUrlState = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [urlState, setUrlState] = useState<UrlState>({});

  // Helper function to check if a value is empty
  const isEmpty = (value: unknown): boolean => {
    if (value === undefined || value === null) return true;
    if (typeof value === 'string') return value.trim() === '';
    if (Array.isArray(value)) return value.length === 0;
    if (typeof value === 'object') {
      if (value instanceof URLSearchParams) return value.toString() === '';
      return Object.keys(value).length === 0;
    }
    return false;
  };

  // Helper function to filter out default facet operators
  const filterDefaultOperators = (operators: Record<string, 'AND' | 'OR'> | undefined): Record<string, 'AND' | 'OR'> | undefined => {
    if (!operators) return undefined;
    
    const filtered = Object.entries(operators).reduce((acc, [key, value]) => {
      if (value !== DEFAULT_FACET_OPERATOR) {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, 'AND' | 'OR'>);

    return Object.keys(filtered).length > 0 ? filtered : undefined;
  };

  // Helper function to merge default operators with URL operators
  const mergeDefaultOperators = (operators: Record<string, 'AND' | 'OR'> | undefined): Record<string, 'AND' | 'OR'> => {
    if (!operators) return {};
    
    return Object.entries(operators).reduce((acc, [key, value]) => {
      acc[key] = value;
      return acc;
    }, {} as Record<string, 'AND' | 'OR'>);
  };

  // Update URL with new state
  const updateUrl = useCallback((newState: Partial<UrlState>) => {
    const searchParams = new URLSearchParams(location.search);
    
    // Filter out default facet operators before updating URL
    const filteredState = {
      ...newState,
      facetOperators: filterDefaultOperators(newState.facetOperators)
    };
    
    // Update or remove parameters based on new state
    Object.entries(filteredState).forEach(([key, value]) => {
      if (isEmpty(value)) {
        searchParams.delete(key);
      } else if (Array.isArray(value)) {
        const filteredValue = value.filter(Boolean);
        if (filteredValue.length > 0) {
          searchParams.set(key, filteredValue.join(','));
        } else {
          searchParams.delete(key);
        }
      } else if (typeof value === 'object') {
        const stringified = JSON.stringify(value);
        if (stringified !== '{}') {
          // Properly encode the JSON string
          searchParams.set(key, encodeURIComponent(stringified));
        } else {
          searchParams.delete(key);
        }
      } else {
        searchParams.set(key, String(value));
      }
    });

    // Always update URL with current parameters
    const newSearchString = searchParams.toString();
    if (newSearchString) {
      navigate(`${location.pathname}?${newSearchString}`, { replace: true });
    } else {
      navigate(location.pathname, { replace: true });
    }
  }, [location.pathname, navigate]);

  // Parse URL parameters on mount and when URL changes
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const newState: UrlState = {};

    // Parse each parameter
    searchParams.forEach((value, key) => {
      if (isEmpty(value)) return;

      if (key === 'page' || key === 'pageSize') {
        const num = parseInt(value, 10);
        if (!isNaN(num)) {
          newState[key] = num;
        }
      } else if (key === 'selectedSpecies' || key === 'selectedTypeStrains') {
        const values = value.split(',').filter(Boolean);
        if (values.length > 0) {
          newState[key] = values;
        }
      } else if (key === 'selectedFacets') {
        try {
          // First try to parse as URL-encoded JSON
          const decoded = decodeURIComponent(value);
          const parsed = JSON.parse(decoded);
          if (typeof parsed === 'object' && parsed !== null && !isEmpty(parsed)) {
            // Ensure all facet values are arrays
            const processedFacets = Object.entries(parsed).reduce((acc, [facetKey, facetValue]) => {
              acc[facetKey] = Array.isArray(facetValue) ? facetValue : [facetValue];
              return acc;
            }, {} as Record<string, string[]>);
            
            newState.selectedFacets = processedFacets;
          }
        } catch {
          // If parsing fails, try to parse as regular JSON
          try {
            const parsed = JSON.parse(value);
            if (typeof parsed === 'object' && parsed !== null && !isEmpty(parsed)) {
              // Ensure all facet values are arrays
              const processedFacets = Object.entries(parsed).reduce((acc, [facetKey, facetValue]) => {
                acc[facetKey] = Array.isArray(facetValue) ? facetValue : [facetValue];
                return acc;
              }, {} as Record<string, string[]>);
              
              newState.selectedFacets = processedFacets;
            }
          } catch {
            // If both parsing attempts fail, ignore the value
            console.warn('Failed to parse selectedFacets from URL:', value);
          }
        }
      } else if (key === 'facetOperators') {
        try {
          // First try to parse as URL-encoded JSON
          const decoded = decodeURIComponent(value);
          const parsed = JSON.parse(decoded);
          if (typeof parsed === 'object' && parsed !== null && !isEmpty(parsed)) {
            // Merge with default operators
            newState.facetOperators = mergeDefaultOperators(parsed);
          }
        } catch {
          // If parsing fails, try to parse as regular JSON
          try {
            const parsed = JSON.parse(value);
            if (typeof parsed === 'object' && parsed !== null && !isEmpty(parsed)) {
              // Merge with default operators
              newState.facetOperators = mergeDefaultOperators(parsed);
            }
          } catch {
            // If both parsing attempts fail, ignore the value
            console.warn('Failed to parse facetOperators from URL:', value);
          }
        }
      } else if (!isEmpty(value)) {
        (newState as Record<string, string>)[key] = value;
      }
    });

    // Ensure facetOperators has default values for any facets that don't specify an operator
    if (newState.selectedFacets) {
      const defaultOperators = Object.keys(newState.selectedFacets).reduce((acc, key) => {
        acc[key] = DEFAULT_FACET_OPERATOR;
        return acc;
      }, {} as Record<string, 'AND' | 'OR'>);

      newState.facetOperators = {
        ...defaultOperators,
        ...newState.facetOperators
      };
    }

    // Only update state if there are actual changes
    if (JSON.stringify(newState) !== JSON.stringify(urlState)) {
      console.log('Updating URL state:', newState);
      setUrlState(newState);
    }
  }, [location.search, urlState]);

  return { urlState, updateUrl };
}; 