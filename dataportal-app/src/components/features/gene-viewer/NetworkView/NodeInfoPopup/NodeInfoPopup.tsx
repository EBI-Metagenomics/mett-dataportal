import React from 'react';
import { PPINetworkNode } from '../../../../../interfaces/PPI';
import styles from './NodeInfoPopup.module.scss';

interface NodeInfoPopupProps {
  node: PPINetworkNode;
  x: number;
  y: number;
  onClose: () => void;
}

export const NodeInfoPopup: React.FC<NodeInfoPopupProps> = ({ node, x, y, onClose }) => {
  return (
    <div className={styles.popupOverlay} onClick={onClose}>
      <div 
        className={styles.popupContent} 
        onClick={(e) => e.stopPropagation()}
        style={{ left: `${x}px`, top: `${y}px` }}
      >
        <button className={styles.closeButton} onClick={onClose} aria-label="Close">×</button>
        <div className={styles.popupHeader}>
          <h3>{node.locus_tag || node.label || node.id}</h3>
        </div>
        <div className={styles.popupBody}>
          {node.name && (
            <div className={styles.infoRow}>
              <span className={styles.label}>Name:</span>
              <span className={styles.value}>{node.name}</span>
            </div>
          )}
          {node.product && (
            <div className={styles.infoRow}>
              <span className={styles.label}>Product:</span>
              <span className={styles.value}>{node.product}</span>
            </div>
          )}
          {node.id && (
            <div className={styles.infoRow}>
              <span className={styles.label}>UniProt ID:</span>
              <span className={styles.value}>{node.id}</span>
            </div>
          )}
          {node.locus_tag && (
            <div className={styles.infoRow}>
              <span className={styles.label}>Locus Tag:</span>
              <span className={styles.value}>{node.locus_tag}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

