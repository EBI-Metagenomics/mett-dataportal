import React from 'react';
import { PyhmmerEvalueType } from '../../../../../utils/pyhmmer/pyhmmerDefaults';
import styles from './ThresholdTypeSelector.module.scss';

interface ThresholdTypeSelectorProps {
    evalueType: PyhmmerEvalueType;
    onEvalueTypeChange: (type: PyhmmerEvalueType) => void;
}

const ThresholdTypeSelector: React.FC<ThresholdTypeSelectorProps> = ({
    evalueType,
    onEvalueTypeChange
}) => {
    return (
        <div className={styles.radioRow}>
            <label className={styles.radioLabel}>
                <input
                    type="radio"
                    className={styles.radioInput}
                    checked={evalueType === 'evalue'}
                    onChange={() => onEvalueTypeChange('evalue')}
                />
                <span className={styles.radioText}>E-value</span>
            </label>
            <label className={styles.radioLabel}>
                <input
                    type="radio"
                    className={styles.radioInput}
                    checked={evalueType === 'bitscore'}
                    onChange={() => onEvalueTypeChange('bitscore')}
                />
                <span className={styles.radioText}>Bit Score</span>
            </label>
        </div>
    );
};

export default ThresholdTypeSelector;
