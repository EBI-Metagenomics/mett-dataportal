import React from 'react';
import { PPINetworkEdge } from '../../../../../interfaces/PPI';
import styles from './EdgeInfoPopup.module.scss';

interface EdgeInfoPopupProps {
  edge: PPINetworkEdge & { edgeType?: string; orthology_type?: string; expansionLevel?: number };
  sourceNode?: { locus_tag?: string; name?: string; product?: string };
  targetNode?: { locus_tag?: string; name?: string; product?: string };
  x: number;
  y: number;
  onClose: () => void;
}

export const EdgeInfoPopup: React.FC<EdgeInfoPopupProps> = ({
  edge,
  sourceNode,
  targetNode,
  x,
  y,
  onClose,
}) => {
  const getEdgeTypeLabel = () => {
    if (edge.edgeType === 'ortholog') {
      return `Ortholog Relationship${edge.orthology_type ? ` (${edge.orthology_type})` : ''}`;
    }
    return 'PPI Interaction';
  };

  return (
    <div className={styles.popupOverlay} onClick={onClose}>
      <div
        className={styles.popupContent}
        onClick={(e) => e.stopPropagation()}
        style={{ left: `${x}px`, top: `${y}px` }}
      >
        <button className={styles.closeButton} onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className={styles.popupHeader}>
          <h3>{getEdgeTypeLabel()}</h3>
          {edge.expansionLevel !== undefined && edge.expansionLevel > 0 && (
            <span className={styles.expansionBadge}>Level {edge.expansionLevel}</span>
          )}
        </div>
        <div className={styles.popupBody}>
          {/* Source Node Info */}
          <div className={styles.nodeSection}>
            <div className={styles.sectionTitle}>Source</div>
            {sourceNode?.locus_tag && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Locus Tag:</span>
                <span className={styles.value}>{sourceNode.locus_tag}</span>
              </div>
            )}
            {sourceNode?.name && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Name:</span>
                <span className={styles.value}>{sourceNode.name}</span>
              </div>
            )}
            {sourceNode?.product && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Product:</span>
                <span className={styles.value}>{sourceNode.product}</span>
              </div>
            )}
          </div>

          {/* Target Node Info */}
          <div className={styles.nodeSection}>
            <div className={styles.sectionTitle}>Target</div>
            {targetNode?.locus_tag && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Locus Tag:</span>
                <span className={styles.value}>{targetNode.locus_tag}</span>
              </div>
            )}
            {targetNode?.name && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Name:</span>
                <span className={styles.value}>{targetNode.name}</span>
              </div>
            )}
            {targetNode?.product && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Product:</span>
                <span className={styles.value}>{targetNode.product}</span>
              </div>
            )}
          </div>

          {/* Edge Properties */}
          <div className={styles.edgeProperties}>
            {edge.weight !== undefined && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Score/Weight:</span>
                <span className={styles.value}>{edge.weight.toFixed(4)}</span>
              </div>
            )}
            {edge.score_type && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Score Type:</span>
                <span className={styles.value}>{edge.score_type}</span>
              </div>
            )}
            {edge.orthology_type && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Orthology Type:</span>
                <span className={styles.value}>{edge.orthology_type}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

