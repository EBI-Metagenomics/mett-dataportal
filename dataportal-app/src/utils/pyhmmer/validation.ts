// Import ValidationError from types
import { ValidationError } from './types';

/**
 * Validate E-value input
 */
export const validateEValue = (value: string, fieldName: string): ValidationError | null => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        return { field: fieldName, message: 'Must be a valid number' };
    }
    if (numValue < 0 || numValue > 100.0) {
        return { field: fieldName, message: 'Must be between 0 and 100.0' };
    }
    return null;
};

/**
 * Validate Bit Score input
 */
export const validateBitScore = (value: string, fieldName: string): ValidationError | null => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        return { field: fieldName, message: 'Must be a valid number' };
    }
    if (numValue < 0.0 || numValue > 1000.0) {
        return { field: fieldName, message: 'Must be between 0.0 and 1000.0' };
    }
    return null;
};

/**
 * Validate Gap Penalty input
 */
export const validateGapPenalty = (value: string, fieldName: string, maxValue: number): ValidationError | null => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        return { field: fieldName, message: 'Must be a valid number' };
    }
    if (numValue < 0 || numValue >= maxValue) {
        return { field: fieldName, message: `Must be between 0 and ${maxValue}` };
    }
    return null;
};

/**
 * Validate cutoff relationships based on threshold type
 */
export const validateCutoffRelationships = (
    evalueType: 'evalue' | 'bitscore',
    significanceSeq: string,
    significanceHit: string,
    reportSeq: string,
    reportHit: string
): ValidationError[] => {
    const errors: ValidationError[] = [];
    
    if (evalueType === 'evalue') {
        const incE = parseFloat(significanceSeq);
        const incdomE = parseFloat(significanceHit);
        const E = parseFloat(reportSeq);
        const domE = parseFloat(reportHit);
        
        if (!isNaN(incE) && !isNaN(E) && incE > E) {
            errors.push({
                field: 'significanceEValueSeq',
                message: 'Significance E-value (Sequence) should be ≤ Report E-value (Sequence)'
            });
        }
        if (!isNaN(incdomE) && !isNaN(domE) && incdomE > domE) {
            errors.push({
                field: 'significanceEValueHit',
                message: 'Significance E-value (Hit) should be ≤ Report E-value (Hit)'
            });
        }
    } else {
        const incT = parseFloat(significanceSeq);
        const incdomT = parseFloat(significanceHit);
        const T = parseFloat(reportSeq);
        const domT = parseFloat(reportHit);
        
        if (!isNaN(incT) && !isNaN(T) && incT < T) {
            errors.push({
                field: 'significanceBitScoreSeq',
                message: 'Significance Bit Score (Sequence) should be ≥ Report Bit Score (Sequence)'
            });
        }
        if (!isNaN(incdomT) && !isNaN(domT) && incdomT < domT) {
            errors.push({
                field: 'significanceBitScoreHit',
                message: 'Significance Bit Score (Hit) should be ≥ Report Bit Score (Hit)'
            });
        }
    }
    
    return errors;
};

/**
 * Validate sequence input
 */
export const validateSequence = (sequence: string): ValidationError | null => {
    if (!sequence || sequence.trim() === '') {
        return { field: 'sequence', message: 'Sequence is required' };
    }

    // Remove FASTA header if present
    const cleanSequence = sequence.replace(/^>.*\n/, '').replace(/\n/g, '').trim();

    if (cleanSequence.length === 0) {
        return { field: 'sequence', message: 'Valid sequence is required' };
    }

    // Basic amino acid validation (allow standard amino acids + X for unknown)
    const validAminoAcids = /^[ACDEFGHIKLMNPQRSTVWYX]+$/i;
    if (!validAminoAcids.test(cleanSequence)) {
        return { field: 'sequence', message: 'Sequence contains invalid amino acid characters' };
    }

    return null;
};

/**
 * Validate database selection
 */
export const validateDatabase = (database: string): ValidationError | null => {
    if (!database || database.trim() === '') {
        return { field: 'database', message: 'Database selection is required' };
    }
    return null;
};

/**
 * Validate threshold value based on type
 */
export const validateThresholdValue = (
    value: string,
    thresholdType: 'evalue' | 'bitscore'
): ValidationError | null => {
    if (thresholdType === 'evalue') {
        return validateEValue(value, 'threshold_value');
    } else {
        return validateBitScore(value, 'threshold_value');
    }
};

/**
 * Comprehensive validation for PyHMMER search request
 */
export const validatePyhmmerSearchRequest = (request: {
    database: string;
    threshold: 'evalue' | 'bitscore';
    threshold_value: string;
    input: string;
    [key: string]: any;
}): ValidationError[] => {
    const errors: ValidationError[] = [];

    // Basic validations
    const dbError = validateDatabase(request.database);
    if (dbError) errors.push(dbError);

    const seqError = validateSequence(request.input);
    if (seqError) errors.push(seqError);

    const thresholdError = validateThresholdValue(request.threshold_value, request.threshold);
    if (thresholdError) errors.push(thresholdError);

    // Add more specific validations as needed
    return errors;
};
