import React, {useRef} from 'react';
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
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    const handleUseExample = (e: React.MouseEvent) => {
        e.preventDefault();
        setSequence(EXAMPLE_SEQUENCE);
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                setSequence(event.target?.result as string || '');
            };
            reader.readAsText(file);
        }
    };

    const handleReset = () => {
        onResetAll();
    };

    return (
        <div className={styles.formSection}>
            <label className={styles.label}>Sequence</label>

            <div className={styles.sequenceContainer}>
                <textarea
                    className={`${styles.textarea} ${sequenceError ? styles.textareaError : ''}`}
                    value={sequence}
                    onChange={e => setSequence(e.target.value)}
                    placeholder="Paste in your sequence, use the example"
                    rows={10}
                />
                {sequenceError && (
                    <div className={styles.errorMessage}>{sequenceError}</div>
                )}

                {/* Help text integrated at the bottom */}
                <div className={styles.helpText}>
                    Paste in your sequence, use the{' '}
                    <a href="#" onClick={handleUseExample} className={styles.exampleLink}>example</a>
                </div>
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