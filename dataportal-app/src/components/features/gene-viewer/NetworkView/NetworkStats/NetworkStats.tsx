import React from 'react';
import { PPINetworkProperties } from '../../../../../interfaces/PPI';
import styles from './NetworkStats.module.scss';

interface NetworkStatsProps {
  properties: PPINetworkProperties;
}

export const NetworkStats: React.FC<NetworkStatsProps> = ({ properties }) => {
  return (
    <div className={styles.networkStats}>
      <div className={styles.statItem}>
        <span className={styles.statLabel}>Nodes:</span>
        <span className={styles.statValue}>{properties.num_nodes}</span>
      </div>
      <div className={styles.statItem}>
        <span className={styles.statLabel}>Edges:</span>
        <span className={styles.statValue}>{properties.num_edges}</span>
      </div>
      {properties.internal_only_edges !== undefined && (
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Internal-only edges:</span>
          <span className={styles.statValue}>{properties.internal_only_edges}</span>
        </div>
      )}
      {properties.avg_degree !== undefined && (
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Avg. degree:</span>
          <span className={styles.statValue}>{properties.avg_degree.toFixed(1)}</span>
        </div>
      )}
      {properties.cross_species_edges !== undefined && (
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Cross-species edges:</span>
          <span className={styles.statValue}>{properties.cross_species_edges}</span>
        </div>
      )}
      {properties.ppi_enrichment_p_value !== undefined && (
        <div className={styles.statItem}>
          <span className={styles.statLabel}>PPI enrichment p-value:</span>
          <span className={styles.statValue}>
            {properties.ppi_enrichment_p_value.toExponential(1)}
          </span>
        </div>
      )}
    </div>
  );
};

