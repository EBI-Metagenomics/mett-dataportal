import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export interface SearchUrlState {
    query?: string;
    page?: number;
    pageSize?: number;
    sortField?: string;
    sortOrder?: 'asc' | 'desc';
    selectedSpecies?: string[];
    selectedGenomes?: string[];
    selectedFacets?: Record<string, string[]>;
    facetOperators?: Record<string, 'AND' | 'OR'>;
}

export function useSearchUrlState() {
    const navigate = useNavigate();
    const location = useLocation();
    const [state, setState] = useState<SearchUrlState>({});

    const updateUrl = useCallback((newState: SearchUrlState) => {
        const searchParams = new URLSearchParams();
        
        // Helper function to check if a value is empty
        const isEmpty = (value: unknown): boolean => {
            if (value === undefined || value === null) return true;
            if (Array.isArray(value)) return value.length === 0;
            if (typeof value === 'object') return Object.keys(value).length === 0;
            if (typeof value === 'string') return value.trim() === '';
            return false;
        };

        // Add non-empty parameters to URL
        Object.entries(newState).forEach(([key, value]) => {
            if (!isEmpty(value)) {
                if (typeof value === 'object') {
                    searchParams.set(key, JSON.stringify(value));
                } else {
                    searchParams.set(key, String(value));
                }
            }
        });

        const newSearchString = searchParams.toString();
        const newUrl = newSearchString ? `${location.pathname}?${newSearchString}` : location.pathname;
        
        navigate(newUrl, { replace: true });
    }, [location.pathname, navigate]);

    // Parse URL parameters on mount and when URL changes
    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);
        const newState: SearchUrlState = {};

        searchParams.forEach((value, key) => {
            try {
                // Try to parse as JSON first
                const parsed = JSON.parse(value);
                if (key === 'page' || key === 'pageSize') {
                    newState[key] = Number(parsed);
                } else {
                    newState[key as keyof SearchUrlState] = parsed;
                }
            } catch {
                // If not JSON, use the value as is
                if (key === 'page' || key === 'pageSize') {
                    const num = Number(value);
                    if (!isNaN(num)) {
                        newState[key] = num;
                    }
                } else if (key === 'sortOrder') {
                    if (value === 'asc' || value === 'desc') {
                        newState[key] = value;
                    }
                } else if (key === 'query' || key === 'sortField') {
                    newState[key] = value;
                }
            }
        });

        setState(newState);
    }, [location.search]);

    return { state, updateUrl };
} 