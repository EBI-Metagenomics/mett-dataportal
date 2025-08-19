/**
 * Validation error interface
 */
export interface ValidationError {
    field: string;
    message: string;
}

/**
 * Database option interface
 */
export interface PyhmmerDatabaseOption {
    id: string;
    name: string;
    description: string;
}

/**
 * Threshold type option interface
 */
export interface PyhmmerThresholdOption {
    value: 'evalue' | 'bitscore';
    label: string;
}

/**
 * Matrix substitution option interface
 */
export interface PyhmmerMXOption {
    value: string;
    label: string;
}

/**
 * Search request interface for compact components
 */
export interface PyhmmerCompactSearchRequest {
    database: string;
    threshold: 'evalue' | 'bitscore';
    threshold_value: string;
    input: string;
    // Optional advanced parameters
    E?: string;
    domE?: string;
    incE?: string;
    incdomE?: string;
    T?: string;
    domT?: string;
    incT?: string;
    incdomT?: string;
    popen?: string;
    pextend?: string;
}

/**
 * Search form state interface
 */
export interface PyhmmerSearchFormState {
    // Basic parameters
    database: string;
    threshold: 'evalue' | 'bitscore';
    threshold_value: string;
    input: string;
    
    // E-value parameters
    significanceEValueSeq: string;
    significanceEValueHit: string;
    reportEValueSeq: string;
    reportEValueHit: string;
    
    // Bit score parameters
    significanceBitScoreSeq: string;
    significanceBitScoreHit: string;
    reportBitScoreSeq: string;
    reportBitScoreHit: string;
    
    // Gap penalties
    gapOpen: string;
    gapExtend: string;
    
    // Matrix substitution
    mx?: string;
}

/**
 * Search results state interface
 */
export interface PyhmmerSearchResultsState {
    results: any[];
    loading: boolean;
    loadingMessage: string;
    error: string | undefined;
    hasResults: boolean;
}

/**
 * Feature panel state interface
 */
export interface PyhmmerFeaturePanelState {
    // Collapsible sections
    expandedSections: Set<string>;
    
    // Search state
    searchState: PyhmmerSearchFormState;
    resultsState: PyhmmerSearchResultsState;
    
    // UI state
    isSearching: boolean;
    showAdvanced: boolean;
}

/**
 * Compact search component props
 */
export interface PyhmmerCompactSearchProps {
    // Initial values
    defaultSequence?: string;
    defaultDatabase?: string;
    defaultThreshold?: 'evalue' | 'bitscore';
    
    // Configuration
    showAdvanced?: boolean;
    showDatabaseSelect?: boolean;
    showThresholdSelect?: boolean;
    
    // Callbacks
    onSearch: (request: PyhmmerCompactSearchRequest) => void;
    onSearchStart?: () => void;
    onSearchComplete?: (results: any[]) => void;
    onError?: (error: string) => void;
    
    // Styling
    compact?: boolean;
    className?: string;
}

/**
 * Compact results component props
 */
export interface PyhmmerCompactResultsProps {
    results: any[];
    loading: boolean;
    error?: string;
    
    // Configuration
    maxResults?: number;
    showPagination?: boolean;
    showDownload?: boolean;
    
    // Callbacks
    onResultClick?: (result: any) => void;
    onDownload?: (format: string) => void;
    
    // Styling
    compact?: boolean;
    className?: string;
}

/**
 * Collapsible section props
 */
export interface CollapsibleSectionProps {
    title: string;
    expanded?: boolean;
    onToggle?: (expanded: boolean) => void;
    children: any; 
    className?: string;
}

/**
 * Search history item interface
 */
export interface SearchHistoryItem {
    jobId: string;
    dateCreated: string;
    date: string;
    database: string;
    threshold: string;
    threshold_value: string;
    input: string;
    query?: string; 
    results?: any[];
}

/**
 * Search history state interface
 */
export interface SearchHistoryState {
    history: SearchHistoryItem[];
    selectedJobId: string | undefined;
    currentSearchJobId: string | undefined;
}

/**
 * API response interfaces
 */
export interface PyhmmerSearchResponse {
    id: string;
}

export interface PyhmmerJobDetailsResponse {
    id: string;
    status: string;
    input: string;
    threshold: string;
    threshold_value: number;
    task?: any;
    database?: any;
}

/**
 * Component size variants
 */
export type PyhmmerComponentSize = 'compact' | 'standard' | 'expanded';

/**
 * Search mode variants
 */
export type PyhmmerSearchMode = 'basic' | 'advanced' | 'expert';

/**
 * Results display mode
 */
export type PyhmmerResultsMode = 'table' | 'cards' | 'list';
