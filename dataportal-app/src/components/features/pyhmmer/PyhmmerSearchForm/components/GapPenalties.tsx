import React from 'react';
import styles from './GapPenalties.module.scss';

interface GapPenaltiesProps {
    gapOpen: string;
    gapExtend: string;
    setGapOpen: (value: string) => void;
    setGapExtend: (value: string) => void;
    getFieldError: (fieldName: string) => string | undefined;
}

const GapPenalties: React.FC<GapPenaltiesProps> = ({
    gapOpen,
    gapExtend,
    setGapOpen,
    setGapExtend,
    getFieldError
}) => {
    return (
        <div className={styles.gapRow}>
            <div>
                <div className={styles.gapLabel}>Open</div>
                <div className={styles.inputContainer}>
                    <input
                        type="number"
                        step="any"
                        value={gapOpen}
                        onChange={e => setGapOpen(e.target.value)}
                        className={`${styles.inputSmall} ${getFieldError('gapOpen') ? styles.inputError : ''}`}
                    />
                    {getFieldError('gapOpen') && (
                        <div className={styles.errorMessage}>{getFieldError('gapOpen')}</div>
                    )}
                </div>
            </div>
            <div>
                <div className={styles.gapLabel}>Extend</div>
                <div className={styles.inputContainer}>
                    <input
                        type="number"
                        step="any"
                        value={gapExtend}
                        onChange={e => setGapExtend(e.target.value)}
                        className={`${styles.inputSmall} ${getFieldError('gapExtend') ? styles.inputError : ''}`}
                    />
                    {getFieldError('gapExtend') && (
                        <div className={styles.errorMessage}>{getFieldError('gapExtend')}</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default GapPenalties;
