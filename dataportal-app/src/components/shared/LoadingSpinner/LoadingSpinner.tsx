import React from 'react'
import styles from './LoadingSpinner.module.scss'

interface LoadingSpinnerProps {
    size?: 'small' | 'medium' | 'large'
    message?: string
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
                                                           size = 'medium',
                                                           message = 'Loading...'
                                                       }) => {
    return (
        <div className={styles.spinnerContainer}>
            <div className={`${styles.spinner} ${styles[size]}`}></div>
            {message && <p className={styles.message}>{message}</p>}
        </div>
    )
}

export default LoadingSpinner
