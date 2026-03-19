import React from 'react';
import { PPINetworkProperties } from '../../../../../interfaces/PPI';
import { NETWORK_VIEW_CONSTANTS, STRING_EVIDENCE_CHANNELS } from '../constants';
import styles from './NetworkStats.module.scss';

type DataSourceOption = 'local' | 'stringdb' | 'both';

interface NetworkStatsProps {
  properties: PPINetworkProperties | null;
  /** When properties are missing/partial, show these counts (e.g. from neighborhood API). */
  nodeCount?: number;
  edgeCount?: number;
  showOrthologs: boolean;
  /** When "both", show legend for Local vs STRING DB edge colors. */
  dataSource?: DataSourceOption;
  /** When STRING DB, show evidence channel colors (multiple edges per pair). */
  showStringEvidenceLegend?: boolean;
}


export const NetworkStats: React.FC<NetworkStatsProps> = ({
  properties,
  nodeCount,
  edgeCount,
  showOrthologs,
  dataSource = 'local',
  showStringEvidenceLegend = false,
}) => {
  // Prefer explicit counts when provided (e.g. enriched graph with expansions); otherwise use properties
  const numNodes = nodeCount ?? properties?.num_nodes ?? 0;
  const numEdges = edgeCount ?? properties?.num_edges ?? 0;

  return (
    <div className={styles.networkStats}>
      <div className={styles.statsLeft}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Nodes:</span>
          <span className={styles.statValue}>{numNodes}</span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Edges:</span>
          <span className={styles.statValue}>{numEdges}</span>
        </div>
        {properties?.internal_only_edges !== undefined && (
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Internal-only edges:</span>
            <span className={styles.statValue}>{properties.internal_only_edges}</span>
          </div>
        )}
        {properties?.avg_degree !== undefined && (
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Avg. degree:</span>
            <span className={styles.statValue}>{properties.avg_degree.toFixed(1)}</span>
          </div>
        )}
        {properties?.cross_species_edges !== undefined && (
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Cross-species edges:</span>
            <span className={styles.statValue}>{properties.cross_species_edges}</span>
          </div>
        )}
        {properties?.ppi_enrichment_p_value !== undefined && (
          <div className={styles.statItem}>
            <span className={styles.statLabel}>PPI enrichment p-value:</span>
            <span className={styles.statValue}>
              {properties.ppi_enrichment_p_value.toExponential(1)}
            </span>
          </div>
        )}
      </div>

      {/* Legend on the right */}
      <div className={styles.legend}>
        {dataSource === 'both' && (
          <>
            <div className={styles.legendItem}>
              <span className={`${styles.legendEdgeLine} ${styles.legendEdgeLocal}`} />
              <span>Local (ES)</span>
            </div>
            {showStringEvidenceLegend
              ? STRING_EVIDENCE_CHANNELS.map((ch) => (
                  <div key={ch.value} className={styles.legendItem}>
                    <span
                      className={styles.legendEdgeLine}
                      data-channel={ch.value}
                    />
                    <span>{ch.label}</span>
                  </div>
                ))
              : (
                <div className={styles.legendItem}>
                  <span className={`${styles.legendEdgeLine} ${styles.legendEdgeStringdb}`} />
                  <span>STRING DB</span>
                </div>
              )}
          </>
        )}
        {dataSource === 'stringdb' && (
          showStringEvidenceLegend ? (
            STRING_EVIDENCE_CHANNELS.map((ch) => (
              <div key={ch.value} className={styles.legendItem}>
                <span
                  className={styles.legendEdgeLine}
                  data-channel={ch.value}
                />
                <span>{ch.label}</span>
              </div>
            ))
          ) : (
            <div className={styles.legendItem}>
              <span className={`${styles.legendEdgeLine} ${styles.legendEdgeStringdb}`} />
              <span>STRING DB</span>
            </div>
          )
        )}
        {dataSource === 'local' && (
          <div className={styles.legendItem}>
            <span className={`${styles.legendColor} ${styles.legendColorPPI}`}></span>
            <span>PPI Interaction</span>
          </div>
        )}
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
            {/* <div className={styles.legendItem}>
              <span className={`${styles.legendColor} ${styles.legendColorOrthologEdge}`}></span>
              <span>Ortholog Relationship</span>
            </div> */}
          </>
        )}
      </div>
    </div>
  );
};

