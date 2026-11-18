import React from 'react';
import styles from './PyhmmerSearchInput.module.scss';
import {EXAMPLE_SEQUENCE} from '../../../../utils/common/constants';

interface PyhmmerSearchInputProps {
    sequence: string;
    setSequence: (value: string) => void;
    handleSubmit: (e?: React.FormEvent) => void;
    sequenceError?: string;
    isFormValid: boolean;
    // Reset functions for all form values
    onResetAll: () => void;
}

const PyhmmerSearchInput: React.FC<PyhmmerSearchInputProps> = ({
    sequence, 
    setSequence, 
    handleSubmit, 
    sequenceError, 
    isFormValid,
    onResetAll
}) => {
    const handleUseExample = (e: React.MouseEvent) => {
        e.preventDefault();
        setSequence(EXAMPLE_SEQUENCE);
    };

    const handleReset = () => {
        onResetAll();
    };

    return (
        <div className={styles.formSection}>
            <div className={styles.labelRow}>
                <label className={styles.label} htmlFor="pyhmmer-sequence">Sequence</label>
                <button type="button" className={styles.exampleLink} onClick={handleUseExample}>
                    Use example
                </button>
            </div>

            <div className={styles.sequenceContainer}>
                <textarea
                    id="pyhmmer-sequence"
                    className={`${styles.textarea} ${sequenceError ? styles.textareaError : ''}`}
                    value={sequence}
                    onChange={e => setSequence(e.target.value)}
                    placeholder="Paste a FASTA protein sequence"
                    rows={3}
                />
                {sequenceError && (
                    <div className={styles.errorMessage}>{sequenceError}</div>
                )}
            </div>

            <div className={styles.buttonRow}>
                <button
                    className="vf-button vf-button--primary vf-button--sm"
                    onClick={handleSubmit}
                    type="button"
                    disabled={!isFormValid}
                >
                    Submit
                </button>
                <button
                    className="vf-button vf-button--sm"
                    type="button"
                    onClick={handleReset}
                >
                    Reset
                </button>
            </div>
        </div>
    );
};

export default PyhmmerSearchInput; 