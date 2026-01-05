import React from 'react';
import styles from './EmptyState.module.scss';

interface EmptyStateProps {
  message?: string;
  hint?: string;
  variant?: 'empty' | 'select-gene' | 'no-species';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  message = 'No network data available for this species.',
  hint = 'Try adjusting the score threshold or selecting a different score type.',
  variant = 'empty',
}) => {
  if (variant === 'select-gene') {
    return (
      <div className={styles.networkViewEmpty}>
        <div className={styles.selectGeneMessage}>
          <div className={styles.selectGeneIcon}>🧬</div>
          <div className={styles.selectGeneContent}>
            <h3>Select a Gene to View Network</h3>
            <p>
              Please select a gene from the search results or genomic context view to visualize its protein-protein interaction network.
            </p>
            <p className={styles.selectGeneHint}>
              The network will show interactions for the selected gene and its immediate neighbors.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.networkViewEmpty}>
      <p>{message}</p>
      {hint && <p className={styles.emptyHint}>{hint}</p>}
    </div>
  );
};

