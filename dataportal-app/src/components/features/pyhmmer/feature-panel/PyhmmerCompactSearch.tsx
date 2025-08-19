import React, {useEffect, useState} from 'react';
import {PyhmmerCompactSearchRequest, validatePyhmmerSearchRequest, ValidationError} from '../../../../utils/pyhmmer';
import {
    PYHMMER_DATABASES,
    PYHMMER_ERROR_MESSAGES,
    PYHMMER_LOADING_MESSAGES
} from '../../../../utils/pyhmmer';
import {PyhmmerService} from '../../../../services/pyhmmer';
import styles from './PyhmmerCompactSearch.module.scss';

interface PyhmmerCompactSearchProps {
    // Initial values
    defaultSequence?: string;
    defaultDatabase?: string;

    // Callbacks
    onSearch: (request: PyhmmerCompactSearchRequest) => void;
    onSearchStart?: () => void;
    onError?: (error: string) => void;

    // Styling
    className?: string;
}

const PyhmmerCompactSearch: React.FC<PyhmmerCompactSearchProps> = ({
                                                                       defaultSequence = '',
                                                                       defaultDatabase = 'bu_all',
                                                                       onSearch,
                                                                       onSearchStart,
                                                                       onError,
                                                                       className = ''
                                                                   }) => {
    // Form state
    const [database, setDatabase] = useState(defaultDatabase);
    const [sequence, setSequence] = useState(defaultSequence);

    // UI state
    const [loading, setLoading] = useState(false);
    const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
    const [databases, setDatabases] = useState<any[]>(PYHMMER_DATABASES);

    // Initialize databases from service
    useEffect(() => {
        const loadDatabases = async () => {
            try {
                const dbList = await PyhmmerService.getDatabases();
                if (dbList && dbList.length > 0) {
                    setDatabases(dbList);
                }
            } catch (error) {
                console.warn('Could not load databases from service, using defaults');
            }
        };

        loadDatabases();
    }, []);


    // Validate form
    const validateForm = (): boolean => {
        const request = {
            database,
            threshold: 'evalue' as const, // Use default threshold
            threshold_value: '0.01', // Use default value
            input: sequence
        };

        const errors = validatePyhmmerSearchRequest(request);
        setValidationErrors(errors);

        return errors.length === 0;
    };

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setLoading(true);
        setValidationErrors([]);

        try {
            // Call onSearchStart callback
            onSearchStart?.();

            // Prepare search request
            const searchRequest: PyhmmerCompactSearchRequest = {
                database,
                threshold: 'evalue' as const,
                threshold_value: '0.01',
                input: sequence
            };

            // Call the onSearch callback
            onSearch(searchRequest);

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : PYHMMER_ERROR_MESSAGES.SEARCH_FAILED;
            setValidationErrors([{field: 'general', message: errorMessage}]);
            onError?.(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    // Handle input changes
    const handleInputChange = (field: string, value: string) => {
        // Clear validation errors for this field
        setValidationErrors(prev => prev.filter(error => error.field !== field));

        switch (field) {
            case 'database':
                setDatabase(value);
                break;
            case 'sequence':
                setSequence(value);
                break;
        }
    };

    // Get error message for a specific field
    const getFieldError = (field: string): string | undefined => {
        return validationErrors.find(error => error.field === field)?.message;
    };

    // Render error message
    const renderError = (field: string) => {
        const error = getFieldError(field);
        return error ? <div className={styles.errorMessage}>{error}</div> : null;
    };

    // Render general errors
    const renderGeneralErrors = () => {
        const generalErrors = validationErrors.filter(error => error.field === 'general');
        if (generalErrors.length === 0) return null;

        return (
            <div className={styles.generalErrors}>
                {generalErrors.map((error, index) => (
                    <div key={index} className={styles.errorMessage}>
                        {error.message}
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className={`${styles.pyhmmerCompactSearch} ${className}`}>
            <form onSubmit={handleSubmit} className={styles.searchForm}>
                {/* Header */}
                <div className={styles.header}>
                    <h3 className={styles.title}>🔍 PyHMMER Search</h3>
                </div>

                {/* General Errors */}
                {renderGeneralErrors()}

                {/* Database Selection */}
                <div className={styles.formGroup}>
                    <label htmlFor="database" className={styles.label}>
                        Database
                    </label>
                    <select
                        id="database"
                        value={database}
                        onChange={(e) => handleInputChange('database', e.target.value)}
                        className={styles.select}
                        disabled={loading}
                    >
                        {databases.map(db => (
                            <option key={db.id} value={db.id}>
                                {db.name}
                            </option>
                        ))}
                    </select>
                    {renderError('database')}
                </div>

                {/* Sequence Info - Show available sequence */}
                <div className={styles.sequenceInfo}>
                    <div className={styles.sequenceStatus}>
                        <span className={styles.statusIcon}>✅</span>
                        <span className={styles.statusText}>
                            Protein sequence available ({sequence.length} amino acids)
                        </span>
                    </div>
                    {sequence && (
                        <div className={styles.sequencePreview}>
                            <span className={styles.previewLabel}>Preview:</span>
                            <span className={styles.previewText}>
                                {sequence.substring(0, 50)}{sequence.length > 50 ? '...' : ''}
                            </span>
                        </div>
                    )}
                </div>

                {/* Submit Button */}
                <div className={styles.submitSection}>
                    <button
                        type="submit"
                        className={styles.submitButton}
                        disabled={loading || !sequence.trim()}
                    >
                        {loading ? PYHMMER_LOADING_MESSAGES.SEARCHING : '🔍 Search Protein Domains'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default PyhmmerCompactSearch;
