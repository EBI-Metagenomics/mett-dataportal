import { useState, useEffect } from 'react';
import { PYHMMER_DEFAULTS, PyhmmerEvalueType } from '../utils/pyhmmer/pyhmmerDefaults';
import { ValidationError, validateEValue, validateBitScore, validateGapPenalty, validateCutoffRelationships } from '../utils/pyhmmer/validation';

export const usePyhmmerSearchForm = () => {
    // Form state
    const [evalueType, setEvalueType] = useState<PyhmmerEvalueType>(PYHMMER_DEFAULTS.EVALUE_TYPE);
    const [sequence, setSequence] = useState('');
    const [database, setDatabase] = useState<string>(PYHMMER_DEFAULTS.DATABASE);

    // Cutoff parameters
    const [significanceEValueSeq, setSignificanceEValueSeq] = useState<string>(PYHMMER_DEFAULTS.SIGNIFICANCE_EVALUE_SEQ);
    const [significanceEValueHit, setSignificanceEValueHit] = useState<string>(PYHMMER_DEFAULTS.SIGNIFICANCE_EVALUE_HIT);
    const [reportEValueSeq, setReportEValueSeq] = useState<string>(PYHMMER_DEFAULTS.REPORT_EVALUE_SEQ);
    const [reportEValueHit, setReportEValueHit] = useState<string>(PYHMMER_DEFAULTS.REPORT_EVALUE_HIT);
    const [significanceBitScoreSeq, setSignificanceBitScoreSeq] = useState<string>(PYHMMER_DEFAULTS.SIGNIFICANCE_BITSCORE_SEQ);
    const [significanceBitScoreHit, setSignificanceBitScoreHit] = useState<string>(PYHMMER_DEFAULTS.SIGNIFICANCE_BITSCORE_HIT);
    const [reportBitScoreSeq, setReportBitScoreSeq] = useState<string>(PYHMMER_DEFAULTS.REPORT_BITSCORE_SEQ);
    const [reportBitScoreHit, setReportBitScoreHit] = useState<string>(PYHMMER_DEFAULTS.REPORT_BITSCORE_HIT);

    // Gap penalties
    const [gapOpen, setGapOpen] = useState<string>(PYHMMER_DEFAULTS.GAP_OPEN);
    const [gapExtend, setGapExtend] = useState<string>(PYHMMER_DEFAULTS.GAP_EXTEND);

    // Validation state
    const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

    // Validation function
    const validateForm = (): ValidationError[] => {
        const errors: ValidationError[] = [];

        // Validate E-value parameters when E-value is selected
        if (evalueType === 'evalue') {
            const incEError = validateEValue(significanceEValueSeq, 'significanceEValueSeq');
            if (incEError) errors.push(incEError);

            const incdomEError = validateEValue(significanceEValueHit, 'significanceEValueHit');
            if (incdomEError) errors.push(incdomEError);

            const EError = validateEValue(reportEValueSeq, 'reportEValueSeq');
            if (EError) errors.push(EError);

            const domEError = validateEValue(reportEValueHit, 'reportEValueHit');
            if (domEError) errors.push(domEError);
        }

        // Validate Bit Score parameters when Bit Score is selected
        if (evalueType === 'bitscore') {
            const incTError = validateBitScore(significanceBitScoreSeq, 'significanceBitScoreSeq');
            if (incTError) errors.push(incTError);

            const incdomTError = validateBitScore(significanceBitScoreHit, 'significanceBitScoreHit');
            if (incdomTError) errors.push(incdomTError);

            const TError = validateBitScore(reportBitScoreSeq, 'reportBitScoreSeq');
            if (TError) errors.push(TError);

            const domTError = validateBitScore(reportBitScoreHit, 'reportBitScoreHit');
            if (domTError) errors.push(domTError);
        }

        // Validate gap penalties
        const gapOpenError = validateGapPenalty(gapOpen, 'gapOpen', 0.5);
        if (gapOpenError) errors.push(gapOpenError);

        const gapExtendError = validateGapPenalty(gapExtend, 'gapExtend', 1.0);
        if (gapExtendError) errors.push(gapExtendError);

        // Validate cutoff relationships
        const relationshipErrors = validateCutoffRelationships(
            evalueType,
            evalueType === 'evalue' ? significanceEValueSeq : significanceBitScoreSeq,
            evalueType === 'evalue' ? significanceEValueHit : significanceBitScoreHit,
            evalueType === 'evalue' ? reportEValueSeq : reportBitScoreSeq,
            evalueType === 'evalue' ? reportEValueHit : reportBitScoreHit
        );
        errors.push(...relationshipErrors);

        return errors;
    };

    // Get error for a specific field
    const getFieldError = (fieldName: string): string | undefined => {
        return validationErrors.find(error => error.field === fieldName)?.message;
    };

    // Check if form is valid
    const isFormValid = (): boolean => {
        return validationErrors.length === 0;
    };

    // Reset form to default values
    const resetForm = () => {
        setEvalueType(PYHMMER_DEFAULTS.EVALUE_TYPE);
        setSequence('');
        setDatabase(PYHMMER_DEFAULTS.DATABASE);

        // Cutoff parameters
        setSignificanceEValueSeq(PYHMMER_DEFAULTS.SIGNIFICANCE_EVALUE_SEQ);
        setSignificanceEValueHit(PYHMMER_DEFAULTS.SIGNIFICANCE_EVALUE_HIT);
        setReportEValueSeq(PYHMMER_DEFAULTS.REPORT_EVALUE_SEQ);
        setReportEValueHit(PYHMMER_DEFAULTS.REPORT_EVALUE_HIT);
        setSignificanceBitScoreSeq(PYHMMER_DEFAULTS.SIGNIFICANCE_BITSCORE_SEQ);
        setSignificanceBitScoreHit(PYHMMER_DEFAULTS.SIGNIFICANCE_BITSCORE_HIT);
        setReportBitScoreSeq(PYHMMER_DEFAULTS.REPORT_BITSCORE_SEQ);
        setReportBitScoreHit(PYHMMER_DEFAULTS.REPORT_BITSCORE_HIT);

        // Gap penalties
        setGapOpen(PYHMMER_DEFAULTS.GAP_OPEN);
        setGapExtend(PYHMMER_DEFAULTS.GAP_EXTEND);

        // Validation errors
        setValidationErrors([]);
    };

    // Update validation errors when form values change
    useEffect(() => {
        const errors = validateForm();
        setValidationErrors(errors);
    }, [
        sequence, evalueType,
        significanceEValueSeq, significanceEValueHit, reportEValueSeq, reportEValueHit,
        significanceBitScoreSeq, significanceBitScoreHit, reportBitScoreSeq, reportBitScoreHit,
        gapOpen, gapExtend
    ]);

    return {
        // Form state
        evalueType,
        setEvalueType,
        sequence,
        setSequence,
        database,
        setDatabase,
        
        // Cutoff parameters
        significanceEValueSeq,
        setSignificanceEValueSeq,
        significanceEValueHit,
        setSignificanceEValueHit,
        reportEValueSeq,
        setReportEValueSeq,
        reportEValueHit,
        setReportEValueHit,
        significanceBitScoreSeq,
        setSignificanceBitScoreSeq,
        significanceBitScoreHit,
        setSignificanceBitScoreHit,
        reportBitScoreSeq,
        setReportBitScoreSeq,
        reportBitScoreHit,
        setReportBitScoreHit,
        
        // Gap penalties
        gapOpen,
        setGapOpen,
        gapExtend,
        setGapExtend,
        
        // Validation
        validationErrors,
        getFieldError,
        isFormValid,
        resetForm
    };
};
