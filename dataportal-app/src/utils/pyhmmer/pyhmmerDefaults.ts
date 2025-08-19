import {PYHMMER_CONSTANTS} from "./pyhmmerConstants";

export const PYHMMER_DEFAULTS = {
    // E-value type
    EVALUE_TYPE: 'evalue' as const,
    
    // Database
    DATABASE: PYHMMER_CONSTANTS.DATABASES.BU_PV_ALL,
    
    // Cutoff parameters - E-value
    SIGNIFICANCE_EVALUE_SEQ: '0.01',
    SIGNIFICANCE_EVALUE_HIT: '0.03',
    REPORT_EVALUE_SEQ: '1',
    REPORT_EVALUE_HIT: '1',
    
    // Cutoff parameters - Bit Score
    SIGNIFICANCE_BITSCORE_SEQ: '25',
    SIGNIFICANCE_BITSCORE_HIT: '22',
    REPORT_BITSCORE_SEQ: '7',
    REPORT_BITSCORE_HIT: '5',
    
    // Gap penalties
    GAP_OPEN: '0.02',
    GAP_EXTEND: '0.4',
    
    // Validation ranges
    VALIDATION: {
        EVALUE: {
            MIN: 0,
            MAX: 100.0
        },
        BITSCORE: {
            MIN: 0.0,
            MAX: 1000.0
        },
        GAP_PENALTY: {
            MAX: 10.0
        }
    },
    
    // JBrowse-specific defaults
    JBROWSE: {
        FEATURE_PANEL: {
            ID: 'pyhmmer-feature-panel',
            TITLE: 'PyHMMER Search',
            ICON: '🔍',
            POSITION: 'right' as const,
            WIDTH: 400,
            HEIGHT: 600,
            COLLAPSIBLE: true,
            DEFAULT_COLLAPSED: false
        },
        PLUGIN: {
            NAME: 'PyHMMER Feature Panel',
            VERSION: '1.0.0',
            DESCRIPTION: 'Protein domain search integration for JBrowse',
            MIN_JBROWSE_VERSION: '2.0.0',
            MAX_JBROWSE_VERSION: '3.0.0'
        }
    },
    
    // Component-specific defaults
    COMPONENTS: {
        COMPACT_SEARCH: {
            SHOW_ADVANCED_PARAMETERS: false,
            MAX_RESULTS: 50,
            AUTO_SEARCH: true
        },
        FEATURE_WIDGET: {
            AUTO_SEARCH: true,
            SHOW_SEQUENCE_PREVIEW: true
        }
    }
} as const;

export type PyhmmerEvalueType = 'evalue' | 'bitscore';
