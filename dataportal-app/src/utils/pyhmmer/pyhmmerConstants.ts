
// PyHMMER help text for popovers
export const PYHMMER_CUTOFF_HELP = `
E-value: Expected number of false positives. Lower values are more stringent (e.g., 0.01 means 1% chance of false positive).

Bit Score: Log-odds score for alignment quality. Higher values indicate better alignments.

Significance: Threshold for including hits in results.

Report: Threshold for reporting hits in output.
`;

export const PYHMMER_GAP_PENALTIES_HELP = `
Gap open and extension penalties control the cost of introducing and extending gaps in the alignment. Lower values allow more gaps; higher values penalize gaps more strongly. Default values are usually appropriate for most searches.
`;

export const PYHMMER_FILTER_HELP = `
The bias composition filter reduces the impact of low-complexity or biased regions in protein sequences, which can otherwise lead to spurious hits. It is recommended to keep this filter enabled unless you have a specific reason to turn it off.
`;

// PyHMMER Constants - Centralized configuration
export const PYHMMER_CONSTANTS = {
    // Database configurations
    DATABASES: {
        BU_ALL: 'bu_all',
        BU_TYPE_STRAINS: 'bu_type_strains',
        PV_ALL: 'pv_all',
        PV_TYPE_STRAINS: 'pv_type_strains',
        BU_PV_TYPE_STRAINS: 'bu_pv_type_strains',
        BU_PV_ALL: 'bu_pv_all',
        DEFAULT: 'bu_pv_all'
    },
    
    // Threshold configurations
    THRESHOLDS: {
        DEFAULT_EVALUE: 0.01,
        DEFAULT_DOM_EVALUE: 0.01,
        DEFAULT_INC_EVALUE: 0.01,
        DEFAULT_INCDOM_EVALUE: 0.03,
        DEFAULT_BITSCORE: 25.0,
        DEFAULT_GAP_OPEN: 0.02,
        DEFAULT_GAP_EXTEND: 0.4
    },
    
    // Validation ranges
    VALIDATION: {
        EVALUE_MIN: 0,
        EVALUE_MAX: 100.0,
        BITSCORE_MIN: 0.0,
        BITSCORE_MAX: 1000.0,
        GAP_PENALTY_MAX: 1.0
    },
    
    // Sequence limits
    SEQUENCE: {
        MAX_LENGTH: 10000,
        MIN_LENGTH: 1,
        MAX_DISPLAY: 50
    },
    
    // Display limits
    DISPLAY: {
        MAX_RESULTS: 100,
        MAX_RESULTS_DISPLAY: 100
    },
    
    // Search history configuration
    HISTORY: {
        CLEANUP_DAYS: 14,
        MAX_ITEMS: 50,
        STORAGE_KEY: 'pyhmmer_search_history'
    },
    
    // UI Colors (matching EMBL-EBI theme)
    COLORS: {
        PRIMARY: '#3b6fb6',
        PRIMARY_HOVER: '#193f90',
        SECONDARY: '#f5f5f5',
        BORDER: '#e5e5e5',
        TEXT_PRIMARY: '#374151',
        TEXT_SECONDARY: '#6b7280'
    },
    
    // Timeouts and intervals
    TIMING: {
        BUTTON_STYLING_TIMEOUT: 10000,
        STYLING_CHECK_INTERVAL: 1000,
        JOB_POLL_INTERVAL: 2000,
        MAX_JOB_POLL_ATTEMPTS: 30,
        STATUS_POLL_INTERVAL: 2000,
        RESULTS_POLL_INTERVAL: 1000,
        SEARCH_TIMEOUT: 300000, // 5 minutes
        REQUEST_TIMEOUT: 30000, // 30 seconds
        SEARCH_DEBOUNCE: 500,
        INPUT_DEBOUNCE: 300
    },
    
    // Button styling
    BUTTON_STYLES: {
        PADDING: '8px 16px',
        BORDER_RADIUS: '6px',
        FONT_SIZE: '14px',
        FONT_WEIGHT: '500',
        MIN_WIDTH: '120px',
        BOX_SHADOW: '0 2px 4px rgba(0, 0, 0, 0.1)',
        BOX_SHADOW_HOVER: '0 4px 8px rgba(0, 0, 0, 0.2)'
    },
    
    // Panel styling
    PANEL_STYLES: {
        MARGIN: '8px 0',
        BORDER_RADIUS: '6px',
        PADDING: '12px',
        HEADER_PADDING: '8px 12px'
    },
    
    // Animation and UI
    UI: {
        ANIMATION_DURATION: 300,
        TRANSITION_DURATION: 200
    },
    
    // Feature panel specific
    FEATURE_PANEL: {
        COMPACT_SEQUENCE_LENGTH: 30,
        COMPACT_RESULTS_COUNT: 10,
        SECTIONS: {
            SEARCH: 'search',
            RESULTS: 'results',
            ADVANCED: 'advanced'
        },
        DEFAULT_EXPANDED: 'search'
    }
} as const;

// Database options for UI components
export const PYHMMER_DATABASES = [
    { id: 'bu_type_strains', name: 'BU Type Strains', description: 'All BU type strain databases' },
    { id: 'bu_all', name: 'BU All Strains', description: 'All BU strain databases' },
    { id: 'pv_all', name: 'PV All Strains', description: 'All PV strain databases' },
    { id: 'pv_type_strains', name: 'PV Type Strains', description: 'All PV type strain databases' },
    { id: 'bu_pv_all', name: 'BU + PV All Strains', description: 'BU and PV strain databases' },
    { id: 'bu_pv_type_strains', name: 'BU PV Type Strains', description: 'BU PV type strain databases' },
];

// Threshold type options
export const PYHMMER_THRESHOLD_TYPES = [
    { value: 'evalue', label: 'E-value' },
    { value: 'bitscore', label: 'Bit Score' }
];

// Matrix substitution options
export const PYHMMER_MX_CHOICES = [
    { value: 'BLOSUM62', label: 'BLOSUM62' },
    { value: 'BLOSUM45', label: 'BLOSUM45' },
    { value: 'BLOSUM80', label: 'BLOSUM80' },
    { value: 'PAM250', label: 'PAM250' },
    { value: 'PAM30', label: 'PAM30' }
];

// Help text for PyHMMER parameters
export const PYHMMER_HELP_TEXT = {
    EVALUE: 'E-value threshold for reporting hits. Lower values are more stringent.',
    BITSCORE: 'Bit score threshold for reporting hits. Higher values are more stringent.',
    GAP_OPEN: 'Gap opening penalty. Higher values discourage gap creation.',
    GAP_EXTEND: 'Gap extension penalty. Higher values discourage long gaps.',
    DATABASE: 'Select the database to search against.',
    SEQUENCE: 'Enter protein sequence in FASTA format or plain text.',
    THRESHOLD: 'Choose between E-value (lower = more stringent) or Bit Score (higher = more stringent).'
};

// Error messages for PyHMMER functionality
export const PYHMMER_ERROR_MESSAGES = {
    SEQUENCE_REQUIRED: 'Protein sequence is required',
    INVALID_SEQUENCE: 'Invalid protein sequence format',
    DATABASE_REQUIRED: 'Database selection is required',
    THRESHOLD_REQUIRED: 'Threshold value is required',
    INVALID_THRESHOLD: 'Invalid threshold value',
    SEARCH_FAILED: 'Search failed. Please try again.',
    NO_RESULTS: 'No results found for the given parameters.',
    NETWORK_ERROR: 'Network error. Please check your connection.',
    VALIDATION_ERROR: 'Please fix the validation errors above.'
};

// Success messages for PyHMMER functionality
export const PYHMMER_SUCCESS_MESSAGES = {
    SEARCH_STARTED: 'Search started successfully',
    SEARCH_COMPLETED: 'Search completed successfully',
    RESULTS_LOADED: 'Results loaded successfully',
    SETTINGS_SAVED: 'Settings saved successfully'
};

// Loading messages for PyHMMER functionality
export const PYHMMER_LOADING_MESSAGES = {
    SEARCHING: 'Searching database...',
    PROCESSING: 'Processing results...',
    LOADING_RESULTS: 'Loading results...',
    INITIALIZING: 'Initializing search...'
};

// Type-safe access to constants
export type PyhmmerDatabase = typeof PYHMMER_CONSTANTS.DATABASES[keyof typeof PYHMMER_CONSTANTS.DATABASES];
export type PyhmmerThreshold = typeof PYHMMER_CONSTANTS.THRESHOLDS[keyof typeof PYHMMER_CONSTANTS.THRESHOLDS];

// Legacy export for backward compatibility (will be removed in future)
export const PYHMMER_CONFIG = {
    SEARCH_HISTORY_CLEANUP_DAYS: PYHMMER_CONSTANTS.HISTORY.CLEANUP_DAYS,
    DEFAULT_EVALUE: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_EVALUE,
    DEFAULT_BITSCORE: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_BITSCORE,
    DEFAULT_GAP_OPEN: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_GAP_OPEN,
    DEFAULT_GAP_EXTEND: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_GAP_EXTEND,
    EVALUE_MIN: PYHMMER_CONSTANTS.VALIDATION.EVALUE_MIN,
    EVALUE_MAX: PYHMMER_CONSTANTS.VALIDATION.EVALUE_MAX,
    BITSCORE_MIN: PYHMMER_CONSTANTS.VALIDATION.BITSCORE_MIN,
    BITSCORE_MAX: PYHMMER_CONSTANTS.VALIDATION.BITSCORE_MAX,
    GAP_PENALTY_MAX: PYHMMER_CONSTANTS.VALIDATION.GAP_PENALTY_MAX,
    MAX_SEQUENCE_LENGTH: PYHMMER_CONSTANTS.SEQUENCE.MAX_LENGTH,
    MIN_SEQUENCE_LENGTH: PYHMMER_CONSTANTS.SEQUENCE.MIN_LENGTH,
    MAX_SEQUENCE_DISPLAY: PYHMMER_CONSTANTS.SEQUENCE.MAX_DISPLAY,
    MAX_RESULTS_DISPLAY: PYHMMER_CONSTANTS.DISPLAY.MAX_RESULTS_DISPLAY,
    HISTORY_KEY: PYHMMER_CONSTANTS.HISTORY.STORAGE_KEY,
    SETTINGS_KEY: 'pyhmmer_user_settings'
};
