import React, { useState, useEffect } from 'react';
import { 
    validatePyhmmerSearchRequest, 
    ValidationError,
    formatValidationErrors,
    PYHMMER_CONFIG,
    PYHMMER_DATABASES,
    PYHMMER_THRESHOLD_TYPES,
    PYHMMER_MX_CHOICES,
    PYHMMER_ERROR_MESSAGES,
    PYHMMER_LOADING_MESSAGES
} from '../../../../utils/pyhmmer';
import { PyhmmerService } from '../../../../services/pyhmmerService';
import { PyhmmerCompactSearchRequest, PyhmmerCompactSearchProps } from '../../../../utils/pyhmmer';
import styles from './PyhmmerSearchCore.module.scss';

const PyhmmerSearchCore: React.FC<PyhmmerCompactSearchProps> = ({
    defaultSequence = '',
    defaultDatabase = 'bu_all',
    defaultThreshold = 'evalue',
    showAdvanced = false,
    showDatabaseSelect = true,
    showThresholdSelect = true,
    onSearch,
    onSearchStart,
    onSearchComplete,
    onError,
    compact = false,
    className = ''
}) => {
    // Form state
    const [database, setDatabase] = useState(defaultDatabase);
    const [threshold, setThreshold] = useState<'evalue' | 'bitscore'>(defaultThreshold);
    const [thresholdValue, setThresholdValue] = useState(
        defaultThreshold === 'evalue' ? '0.01' : '25.0'
    );
    const [sequence, setSequence] = useState(defaultSequence);
    
    // Advanced parameters
    const [showAdvancedParams, setShowAdvancedParams] = useState(showAdvanced);
    const [E, setE] = useState('1.0');
    const [domE, setDomE] = useState('1.0');
    const [incE, setIncE] = useState('0.01');
    const [incdomE, setIncdomE] = useState('0.03');
    const [T, setT] = useState('7.0');
    const [domT, setDomT] = useState('5.0');
    const [incT, setIncT] = useState('25.0');
    const [incdomT, setIncdomT] = useState('22.0');
    const [gapOpen, setGapOpen] = useState('0.02');
    const [gapExtend, setGapExtend] = useState('0.4');
    const [mx, setMx] = useState('BLOSUM62');
    
    // UI state
    const [loading, setLoading] = useState(false);
    const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
    const [databases, setDatabases] = useState(PYHMMER_DATABASES);
    
    // Initialize databases from service
    useEffect(() => {
        const loadDatabases = async () => {
            try {
                const service = new PyhmmerService();
                const dbList = await service.getDatabases();
                if (dbList && dbList.length > 0) {
                    setDatabases(dbList);
                }
            } catch (error) {
                console.warn('Could not load databases from service, using defaults');
            }
        };
        
        loadDatabases();
    }, []);
    
    // Update threshold value when threshold type changes
    useEffect(() => {
        if (threshold === 'evalue') {
            setThresholdValue('0.01');
        } else {
            setThresholdValue('25.0');
        }
    }, [threshold]);
    
    // Validate form
    const validateForm = (): boolean => {
        const request = {
            database,
            threshold,
            threshold_value: thresholdValue,
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
                threshold,
                threshold_value: thresholdValue,
                input: sequence,
                // Add advanced parameters if showing advanced
                ...(showAdvancedParams && {
                    E,
                    domE,
                    incE,
                    incdomE,
                    T,
                    domT,
                    incT,
                    incdomT,
                    popen: gapOpen,
                    pextend: gapExtend
                })
            };
            
            // Call the onSearch callback
            onSearch(searchRequest);
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : PYHMMER_ERROR_MESSAGES.SEARCH_FAILED;
            setValidationErrors([{ field: 'general', message: errorMessage }]);
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
            case 'threshold':
                setThreshold(value as 'evalue' | 'bitscore');
                break;
            case 'threshold_value':
                setThresholdValue(value);
                break;
            case 'sequence':
                setSequence(value);
                break;
            case 'E':
                setE(value);
                break;
            case 'domE':
                setDomE(value);
                break;
            case 'incE':
                setIncE(value);
                break;
            case 'incdomE':
                setIncdomE(value);
                break;
            case 'T':
                setT(value);
                break;
            case 'domT':
                setDomT(value);
                break;
            case 'incT':
                setIncT(value);
                break;
            case 'incdomT':
                setIncdomT(value);
                break;
            case 'gapOpen':
                setGapOpen(value);
                break;
            case 'gapExtend':
                setGapExtend(value);
                break;
            case 'mx':
                setMx(value);
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
        <div className={`${styles.pyhmmerSearchCore} ${compact ? styles.compact : ''} ${className}`}>
            <form onSubmit={handleSubmit} className={styles.searchForm}>
                {/* General Errors */}
                {renderGeneralErrors()}
                
                {/* Basic Search Parameters */}
                <div className={styles.basicParams}>
                    {/* Database Selection */}
                    {showDatabaseSelect && (
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
                    )}
                    
                    {/* Threshold Type */}
                    {showThresholdSelect && (
                        <div className={styles.formGroup}>
                            <label htmlFor="threshold" className={styles.label}>
                                Threshold Type
                            </label>
                            <select
                                id="threshold"
                                value={threshold}
                                onChange={(e) => handleInputChange('threshold', e.target.value)}
                                className={styles.select}
                                disabled={loading}
                            >
                                {PYHMMER_THRESHOLD_TYPES.map(type => (
                                    <option key={type.value} value={type.value}>
                                        {type.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                    
                    {/* Threshold Value */}
                    <div className={styles.formGroup}>
                        <label htmlFor="threshold_value" className={styles.label}>
                            {threshold === 'evalue' ? 'E-value' : 'Bit Score'}
                        </label>
                        <input
                            type="text"
                            id="threshold_value"
                            value={thresholdValue}
                            onChange={(e) => handleInputChange('threshold_value', e.target.value)}
                            className={styles.input}
                            placeholder={threshold === 'evalue' ? '0.01' : '25.0'}
                            disabled={loading}
                        />
                        {renderError('threshold_value')}
                    </div>
                    
                    {/* Sequence Input */}
                    <div className={styles.formGroup}>
                        <label htmlFor="sequence" className={styles.label}>
                            Protein Sequence
                        </label>
                        <textarea
                            id="sequence"
                            value={sequence}
                            onChange={(e) => handleInputChange('sequence', e.target.value)}
                            className={styles.textarea}
                            placeholder="Enter protein sequence in FASTA format or plain text..."
                            rows={compact ? 3 : 5}
                            disabled={loading}
                        />
                        {renderError('sequence')}
                    </div>
                </div>
                
                {/* Advanced Parameters Toggle */}
                <div className={styles.advancedToggle}>
                    <button
                        type="button"
                        onClick={() => setShowAdvancedParams(!showAdvancedParams)}
                        className={styles.toggleButton}
                        disabled={loading}
                    >
                        {showAdvancedParams ? 'Hide' : 'Show'} Advanced Parameters
                    </button>
                </div>
                
                {/* Advanced Parameters */}
                {showAdvancedParams && (
                    <div className={styles.advancedParams}>
                        <div className={styles.advancedSection}>
                            <h4 className={styles.sectionTitle}>
                                {threshold === 'evalue' ? 'E-value Parameters' : 'Bit Score Parameters'}
                            </h4>
                            
                            {threshold === 'evalue' ? (
                                // E-value parameters
                                <div className={styles.paramGrid}>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="E">Report E-value (Sequence)</label>
                                        <input
                                            type="text"
                                            id="E"
                                            value={E}
                                            onChange={(e) => handleInputChange('E', e.target.value)}
                                            className={styles.input}
                                            disabled={loading}
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="domE">Report E-value (Hit)</label>
                                        <input
                                            type="text"
                                            id="domE"
                                            value={domE}
                                            onChange={(e) => handleInputChange('domE', e.target.value)}
                                            className={styles.input}
                                            disabled={loading}
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="incE">Significance E-value (Sequence)</label>
                                        <input
                                            type="text"
                                            id="incE"
                                            value={incE}
                                            onChange={(e) => handleInputChange('incE', e.target.value)}
                                            className={styles.input}
                                            disabled={loading}
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="incdomE">Significance E-value (Hit)</label>
                                        <input
                                            type="text"
                                            id="incdomE"
                                            value={incdomE}
                                            onChange={(e) => handleInputChange('incdomE', e.target.value)}
                                            className={styles.input}
                                            disabled={loading}
                                        />
                                    </div>
                                </div>
                            ) : (
                                // Bit score parameters
                                <div className={styles.paramGrid}>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="T">Report Bit Score (Sequence)</label>
                                        <input
                                            type="text"
                                            id="T"
                                            value={T}
                                            onChange={(e) => handleInputChange('T', e.target.value)}
                                            className={styles.input}
                                            disabled={loading}
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="domT">Report Bit Score (Hit)</label>
                                        <input
                                            type="text"
                                            id="domT"
                                            value={domT}
                                            onChange={(e) => handleInputChange('domT', e.target.value)}
                                            className={styles.input}
                                            disabled={loading}
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="incT">Significance Bit Score (Sequence)</label>
                                        <input
                                            type="text"
                                            id="incT"
                                            value={incT}
                                            onChange={(e) => handleInputChange('incT', e.target.value)}
                                            className={styles.input}
                                            disabled={loading}
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="incdomT">Significance Bit Score (Hit)</label>
                                        <input
                                            type="text"
                                            id="incdomT"
                                            value={incdomT}
                                            onChange={(e) => handleInputChange('incdomT', e.target.value)}
                                            className={styles.input}
                                            disabled={loading}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                        
                        {/* Gap Penalties */}
                        <div className={styles.advancedSection}>
                            <h4 className={styles.sectionTitle}>Gap Penalties</h4>
                            <div className={styles.paramGrid}>
                                <div className={styles.formGroup}>
                                    <label htmlFor="gapOpen">Gap Open Penalty</label>
                                    <input
                                        type="text"
                                        id="gapOpen"
                                        value={gapOpen}
                                        onChange={(e) => handleInputChange('gapOpen', e.target.value)}
                                        className={styles.input}
                                        disabled={loading}
                                    />
                                </div>
                                <div className={styles.formGroup}>
                                    <label htmlFor="gapExtend">Gap Extension Penalty</label>
                                    <input
                                        type="text"
                                        id="gapExtend"
                                        value={gapExtend}
                                        onChange={(e) => handleInputChange('gapExtend', e.target.value)}
                                        className={styles.input}
                                        disabled={loading}
                                    />
                                </div>
                            </div>
                        </div>
                        
                        {/* Matrix Substitution */}
                        <div className={styles.advancedSection}>
                            <h4 className={styles.sectionTitle}>Matrix Substitution</h4>
                            <div className={styles.formGroup}>
                                <select
                                    value={mx}
                                    onChange={(e) => handleInputChange('mx', e.target.value)}
                                    className={styles.select}
                                    disabled={loading}
                                >
                                    {PYHMMER_MX_CHOICES.map(choice => (
                                        <option key={choice.value} value={choice.value}>
                                            {choice.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>
                )}
                
                {/* Submit Button */}
                <div className={styles.submitSection}>
                    <button
                        type="submit"
                        className={styles.submitButton}
                        disabled={loading || !sequence.trim()}
                    >
                        {loading ? PYHMMER_LOADING_MESSAGES.SEARCHING : 'Search with PyHMMER'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default PyhmmerSearchCore;
