import React from 'react';
import styles from './PyhmmerSearchInput.module.scss';
import {EXAMPLE_SEQUENCE} from '../../../../utils/common/constants';

interface PyhmmerSearchInputProps {
    sequence: string;
    setSequence: (value: string) => void;
    sequenceError?: string;
}

const PyhmmerSearchInput: React.FC<PyhmmerSearchInputProps> = ({
    sequence,
    setSequence,
    sequenceError,
}) => {
    const handleUseExample = (e: React.MouseEvent) => {
        e.preventDefault();
        setSequence(EXAMPLE_SEQUENCE);
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
        </div>
    );
};

export default PyhmmerSearchInput; 