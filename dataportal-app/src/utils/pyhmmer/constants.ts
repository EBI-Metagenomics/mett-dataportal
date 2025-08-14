export const PYHMMER_CONFIG = {
    // Search history cleanup (in days)
    SEARCH_HISTORY_CLEANUP_DAYS: 14,
    
    // Default values
    DEFAULT_EVALUE: 0.01,
    DEFAULT_BITSCORE: 25.0,
    DEFAULT_GAP_OPEN: 0.02,
    DEFAULT_GAP_EXTEND: 0.4,
    
    // Validation ranges
    EVALUE_MIN: 0,
    EVALUE_MAX: 100.0,
    BITSCORE_MIN: 0.0,
    BITSCORE_MAX: 1000.0,
    GAP_PENALTY_MAX: 1.0,
    
    // Sequence limits
    MAX_SEQUENCE_LENGTH: 10000,
    MIN_SEQUENCE_LENGTH: 1,
    
    // Display limits
    MAX_SEQUENCE_DISPLAY: 50,
    MAX_RESULTS_DISPLAY: 100,
    
    // Local storage keys
    HISTORY_KEY: 'pyhmmer_search_history',
    SETTINGS_KEY: 'pyhmmer_user_settings'
};

/**
 * Database options for PyHMMER search
 */
export const PYHMMER_DATABASES = [
    { id: 'bu_all', name: 'BU All Strains', description: 'All BU strain databases' },
    { id: 'bu_pv_all', name: 'BU + PV All Strains', description: 'BU and PV strain databases' },
    { id: 'bu_atcc', name: 'BU ATCC Strains', description: 'BU ATCC strain databases' },
    { id: 'pv_all', name: 'PV All Strains', description: 'All PV strain databases' }
];

/**
 * Threshold type options
 */
export const PYHMMER_THRESHOLD_TYPES = [
    { value: 'evalue', label: 'E-value' },
    { value: 'bitscore', label: 'Bit Score' }
];

/**
 * Matrix substitution options
 */
export const PYHMMER_MX_CHOICES = [
    { value: 'BLOSUM62', label: 'BLOSUM62' },
    { value: 'BLOSUM45', label: 'BLOSUM45' },
    { value: 'BLOSUM80', label: 'BLOSUM80' },
    { value: 'PAM250', label: 'PAM250' },
    { value: 'PAM30', label: 'PAM30' }
];

/**
 * Help text for PyHMMER parameters
 */
export const PYHMMER_HELP_TEXT = {
    EVALUE: 'E-value threshold for reporting hits. Lower values are more stringent.',
    BITSCORE: 'Bit score threshold for reporting hits. Higher values are more stringent.',
    GAP_OPEN: 'Gap opening penalty. Higher values discourage gap creation.',
    GAP_EXTEND: 'Gap extension penalty. Higher values discourage long gaps.',
    DATABASE: 'Select the database to search against.',
    SEQUENCE: 'Enter protein sequence in FASTA format or plain text.',
    THRESHOLD: 'Choose between E-value (lower = more stringent) or Bit Score (higher = more stringent).'
};

/**
 * Error messages for PyHMMER functionality
 */
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

/**
 * Success messages for PyHMMER functionality
 */
export const PYHMMER_SUCCESS_MESSAGES = {
    SEARCH_STARTED: 'Search started successfully',
    SEARCH_COMPLETED: 'Search completed successfully',
    RESULTS_LOADED: 'Results loaded successfully',
    SETTINGS_SAVED: 'Settings saved successfully'
};

/**
 * Loading messages for PyHMMER functionality
 */
export const PYHMMER_LOADING_MESSAGES = {
    SEARCHING: 'Searching database...',
    PROCESSING: 'Processing results...',
    LOADING_RESULTS: 'Loading results...',
    INITIALIZING: 'Initializing search...'
};

/**
 * UI constants for PyHMMER components
 */
export const PYHMMER_UI = {
    // Animation durations
    ANIMATION_DURATION: 300,
    TRANSITION_DURATION: 200,
    
    // Debounce delays
    SEARCH_DEBOUNCE: 500,
    INPUT_DEBOUNCE: 300,
    
    // Polling intervals
    STATUS_POLL_INTERVAL: 2000,
    RESULTS_POLL_INTERVAL: 1000,
    
    // Timeout values
    SEARCH_TIMEOUT: 300000, // 5 minutes
    REQUEST_TIMEOUT: 30000, // 30 seconds
};

/**
 * Feature panel specific constants
 */
export const PYHMMER_FEATURE_PANEL = {
    // Compact mode settings
    COMPACT_SEQUENCE_LENGTH: 30,
    COMPACT_RESULTS_COUNT: 10,
    
    // Collapsible sections
    SECTIONS: {
        SEARCH: 'search',
        RESULTS: 'results',
        ADVANCED: 'advanced'
    },
    
    // Default expanded state
    DEFAULT_EXPANDED: 'search'
};
