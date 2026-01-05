import React from 'react';
import styles from './NetworkLegend.module.scss';

interface NetworkLegendProps {
  showOrthologs: boolean;
}

export const NetworkLegend: React.FC<NetworkLegendProps> = ({ showOrthologs }) => {
  return (
    <div className={styles.legend}>
      <div className={styles.legendItem}>
        <span className={`${styles.legendColor} ${styles.legendColorPPI}`}></span>
        <span>PPI Interaction</span>
      </div>
      {showOrthologs && (
        <>
          <div className={styles.legendItem}>
            <span className={`${styles.legendColor} ${styles.legendColorPPIWithOrthologs}`}></span>
            <span>PPI Node with Orthologs</span>
          </div>
          <div className={styles.legendItem}>
            <span className={`${styles.legendColor} ${styles.legendColorOrtholog}`}></span>
            <span>Ortholog Node</span>
          </div>
          <div className={styles.legendItem}>
            <span className={`${styles.legendColor} ${styles.legendColorOrthologEdge}`}></span>
            <span>Ortholog Relationship</span>
          </div>
        </>
      )}
    </div>
  );
};

