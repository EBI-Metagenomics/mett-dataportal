# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.



### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm test`

Run all tests

### `npm run test:watch`

Run tests in watch mode

### `npm run lint`

Run ESLint on source files

### `npx eslint src/components/Filters/SpeciesFilter.test.tsx`

Lint specific test file


## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)


# React Application Restructuring Plan

## Overview
This document outlines the architectural changes needed to improve the React application's maintainability, extensibility, and user experience, particularly focusing on URL state management for filter sharing.

## Current Issues

### 1. **Monolithic Components**
- `HomePage.tsx` (319 lines) and `GeneViewerPage.tsx` (422 lines) are too large
- Multiple responsibilities: UI rendering, state management, data fetching, business logic
- Difficult to test and maintain

### 2. **Scattered State Management**
- Multiple `useState` hooks managing related data
- No centralized state for shared data (species, genomes, filters)
- State synchronization issues between components

### 3. **No URL State Synchronization**
- Filters and search parameters not reflected in URLs
- Users cannot share filtered views
- Browser back/forward navigation doesn't work with filters

### 4. **Poor Separation of Concerns**
- UI logic mixed with business logic
- Data fetching logic scattered across components
- No clear data flow patterns

## Proposed Architecture

### 1. **State Management with Zustand**

```typescript
// stores/filterStore.ts
interface FilterState {
  // Genome filters
  selectedSpecies: string[]
  selectedTypeStrains: string[]
  genomeSearchQuery: string
  genomeSortField: string
  genomeSortOrder: 'asc' | 'desc'
  
  // Gene filters
  geneSearchQuery: string
  geneSortField: string
  geneSortOrder: 'asc' | 'desc'
  
  // Actions
  setSelectedSpecies: (species: string[]) => void
  setSelectedTypeStrains: (strains: string[]) => void
  setGenomeSearchQuery: (query: string) => void
  // ... other actions
}
```

### 2. **URL State Management**

```typescript
// hooks/useUrlState.ts
export const useUrlState = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  
  const updateUrl = (updates: Record<string, string | string[]>) => {
    const newParams = new URLSearchParams(searchParams)
    
    Object.entries(updates).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        newParams.delete(key)
        value.forEach(v => newParams.append(key, v))
      } else {
        newParams.set(key, value)
      }
    })
    
    setSearchParams(newParams)
  }
  
  return { searchParams, updateUrl }
}
```

### 3. **Component Structure**

```
src/
├── components/
│   ├── layout/
│   │   ├── Header/
│   │   ├── Footer/
│   │   └── Navigation/
│   ├── shared/
│   │   ├── LoadingSpinner/
│   │   ├── ErrorBoundary/
│   │   └── DataTable/
│   └── features/
│       ├── genome/
│       │   ├── GenomeSearch/
│       │   ├── GenomeList/
│       │   └── GenomeFilters/
│       ├── gene/
│       │   ├── GeneSearch/
│       │   ├── GeneViewer/
│       │   └── GeneList/
│       └── search/
│           ├── SearchForm/
│           └── SearchResults/
├── hooks/
│   ├── useUrlState.ts
│   ├── useGenomeData.ts
│   ├── useGeneData.ts
│   └── useSearch.ts
├── stores/
│   ├── filterStore.ts
│   ├── genomeStore.ts
│   └── geneStore.ts
├── services/
│   ├── api/
│   ├── genomeService.ts
│   ├── geneService.ts
│   └── speciesService.ts
├── utils/
│   ├── urlHelpers.ts
│   ├── dataTransformers.ts
│   └── constants.ts
└── pages/
    ├── HomePage.tsx
    ├── GeneViewerPage.tsx
    └── SearchPage.tsx
```

### 4. **Custom Hooks for Business Logic**

```typescript
// hooks/useGenomeData.ts
export const useGenomeData = () => {
  const { selectedSpecies, genomeSearchQuery, genomeSortField, genomeSortOrder } = useFilterStore()
  const [genomes, setGenomes] = useState([])
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    const fetchGenomes = async () => {
      setLoading(true)
      try {
        const response = await GenomeService.fetchGenomesBySearch(
          selectedSpecies, 
          genomeSearchQuery, 
          genomeSortField, 
          genomeSortOrder
        )
        setGenomes(response.results)
      } catch (error) {
        console.error('Error fetching genomes:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchGenomes()
  }, [selectedSpecies, genomeSearchQuery, genomeSortField, genomeSortOrder])
  
  return { genomes, loading }
}
```

### 5. **URL Synchronization Implementation**

```typescript
// hooks/useFilterSync.ts
export const useFilterSync = () => {
  const { searchParams, updateUrl } = useUrlState()
  const filterStore = useFilterStore()
  
  // Sync URL to store on mount
  useEffect(() => {
    const species = searchParams.getAll('species')
    const typeStrains = searchParams.getAll('typeStrains')
    const searchQuery = searchParams.get('search') || ''
    
    filterStore.setSelectedSpecies(species)
    filterStore.setSelectedTypeStrains(typeStrains)
    filterStore.setGenomeSearchQuery(searchQuery)
  }, [])
  
  // Sync store to URL on changes
  useEffect(() => {
    const updates = {
      species: filterStore.selectedSpecies,
      typeStrains: filterStore.selectedTypeStrains,
      search: filterStore.genomeSearchQuery
    }
    updateUrl(updates)
  }, [filterStore.selectedSpecies, filterStore.selectedTypeStrains, filterStore.genomeSearchQuery])
}
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. Install and configure Zustand
2. Create basic stores (filterStore, genomeStore, geneStore)
3. Implement URL state management hooks
4. Set up new folder structure

### Phase 2: Component Extraction (Week 2)
1. Break down HomePage into smaller components
2. Extract business logic into custom hooks
3. Implement filter synchronization
4. Create reusable UI components

### Phase 3: Gene Viewer Refactoring (Week 3)
1. Refactor GeneViewerPage
2. Extract gene-specific logic into hooks
3. Implement URL state for gene viewer
4. Improve error handling

### Phase 4: Testing and Optimization (Week 4)
1. Add comprehensive tests
2. Optimize performance
3. Implement proper error boundaries
4. Add loading states and user feedback

## Benefits of This Restructuring

### 1. **Improved Maintainability**
- Smaller, focused components
- Clear separation of concerns
- Reusable business logic

### 2. **Better User Experience**
- Shareable URLs with filters
- Browser navigation support
- Consistent loading states

### 3. **Enhanced Extensibility**
- Modular architecture
- Easy to add new features
- Scalable state management

### 4. **Better Testing**
- Isolated business logic
- Testable custom hooks
- Clear component boundaries

### 5. **Performance Improvements**
- Reduced re-renders
- Better caching strategies
- Optimized data fetching

## Migration Strategy

### 1. **Gradual Migration**
- Implement new architecture alongside existing code
- Migrate one feature at a time
- Maintain backward compatibility

### 2. **Feature Flags**
- Use feature flags for new implementations
- Easy rollback if issues arise
- A/B testing capabilities

### 3. **Backward Compatibility**
- Keep existing API endpoints
- Maintain current URL structure
- Gradual deprecation of old patterns

## Dependencies to Add

```json
{
  "zustand": "^4.4.0",
  "react-query": "^3.39.0",
  "@tanstack/react-query": "^4.29.0"
}
```

## Next Steps

1. **Review and approve this plan**
2. **Set up development environment**
3. **Begin Phase 1 implementation**
4. **Create detailed component specifications**
5. **Set up testing framework**

This restructuring will transform your application from a monolithic structure to a modern, maintainable, and extensible React application with proper state management and URL synchronization.