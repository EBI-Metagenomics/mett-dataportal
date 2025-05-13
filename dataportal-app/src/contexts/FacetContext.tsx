import React, { createContext, useContext, useReducer, useCallback } from 'react';

interface FacetState {
  selectedFacets: Record<string, string[]>;
  facetOperators: Record<string, 'AND' | 'OR'>;
  collapsedGroups: Record<string, boolean>;
  visibleCounts: Record<string, number>;
  filterTexts: Record<string, string>;
}

type FacetAction =
  | { type: 'TOGGLE_FACET'; group: string; value: string }
  | { type: 'SET_OPERATOR'; group: string; operator: 'AND' | 'OR' }
  | { type: 'TOGGLE_COLLAPSE'; group: string }
  | { type: 'SET_VISIBLE_COUNT'; group: string; count: number }
  | { type: 'SET_FILTER_TEXT'; group: string; text: string };

const initialState: FacetState = {
  selectedFacets: {},
  facetOperators: {},
  collapsedGroups: {},
  visibleCounts: {},
  filterTexts: {},
};

function facetReducer(state: FacetState, action: FacetAction): FacetState {
  switch (action.type) {
    case 'TOGGLE_FACET': {
      const { group, value } = action;
      const currentFacets = state.selectedFacets[group] || [];
      const newFacets = currentFacets.includes(value)
        ? currentFacets.filter(v => v !== value)
        : [...currentFacets, value];

      return {
        ...state,
        selectedFacets: {
          ...state.selectedFacets,
          [group]: newFacets,
        },
      };
    }

    case 'SET_OPERATOR': {
      const { group, operator } = action;
      return {
        ...state,
        facetOperators: {
          ...state.facetOperators,
          [group]: operator,
        },
      };
    }

    case 'TOGGLE_COLLAPSE': {
      const { group } = action;
      return {
        ...state,
        collapsedGroups: {
          ...state.collapsedGroups,
          [group]: !state.collapsedGroups[group],
        },
      };
    }

    case 'SET_VISIBLE_COUNT': {
      const { group, count } = action;
      return {
        ...state,
        visibleCounts: {
          ...state.visibleCounts,
          [group]: count,
        },
      };
    }

    case 'SET_FILTER_TEXT': {
      const { group, text } = action;
      return {
        ...state,
        filterTexts: {
          ...state.filterTexts,
          [group]: text,
        },
      };
    }

    default:
      return state;
  }
}

interface FacetContextType {
  state: FacetState;
  toggleFacet: (group: string, value: string) => void;
  setOperator: (group: string, operator: 'AND' | 'OR') => void;
  toggleCollapse: (group: string) => void;
  setVisibleCount: (group: string, count: number) => void;
  setFilterText: (group: string, text: string) => void;
}

const FacetContext = createContext<FacetContextType | undefined>(undefined);

export function FacetProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(facetReducer, initialState);

  const toggleFacet = useCallback((group: string, value: string) => {
    dispatch({ type: 'TOGGLE_FACET', group, value });
  }, []);

  const setOperator = useCallback((group: string, operator: 'AND' | 'OR') => {
    dispatch({ type: 'SET_OPERATOR', group, operator });
  }, []);

  const toggleCollapse = useCallback((group: string) => {
    dispatch({ type: 'TOGGLE_COLLAPSE', group });
  }, []);

  const setVisibleCount = useCallback((group: string, count: number) => {
    dispatch({ type: 'SET_VISIBLE_COUNT', group, count });
  }, []);

  const setFilterText = useCallback((group: string, text: string) => {
    dispatch({ type: 'SET_FILTER_TEXT', group, text });
  }, []);

  const value = {
    state,
    toggleFacet,
    setOperator,
    toggleCollapse,
    setVisibleCount,
    setFilterText,
  };

  return (
    <FacetContext.Provider value={value}>
      {children}
    </FacetContext.Provider>
  );
}

export function useFacets() {
  const context = useContext(FacetContext);
  if (context === undefined) {
    throw new Error('useFacets must be used within a FacetProvider');
  }
  return context;
} 