import React from 'react';
import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';
import { canExpandNode, getNodeExpansionLevel } from '../utils/expansionUtils';
import { ExpansionState } from '../types/expansion';
import styles from './NodeInfoPopup.module.scss';

interface NodeInfoPopupProps {
  node: PPINetworkNode;
  x: number;
  y: number;
  expansionState?: ExpansionState;
  interactions?: Array<PPINetworkEdge & { edgeType?: string; orthology_type?: string }>;
  connectedNodes?: Map<string, PPINetworkNode>;
  onClose: () => void;
  onExpand?: (node: PPINetworkNode) => void;
  isExpanding?: boolean;
}

export const NodeInfoPopup: React.FC<NodeInfoPopupProps> = ({ 
  node, 
  x, 
  y, 
  expansionState,
  interactions = [],
  connectedNodes = new Map(),
  onClose, 
  onExpand,
  isExpanding = false,
}) => {
  const canExpand = expansionState && canExpandNode(expansionState.path.currentLevel);
  const expansionLevel = expansionState ? getNodeExpansionLevel(expansionState, node.id) : undefined;
  const isExpanded = expansionLevel !== undefined;
  
  // Separate PPI and ortholog interactions
  const ppiInteractions = interactions.filter(e => !e.edgeType || e.edgeType === 'ppi');
  const orthologInteractions = interactions.filter(e => e.edgeType === 'ortholog');

  const handleExpand = () => {
    if (onExpand && canExpand && !isExpanding) {
      // Close popup immediately when expansion starts
      onClose();
      // Then trigger expansion
      onExpand(node);
    }
  };

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
          {isExpanded && (
            <span className={styles.expandedBadge}>Expanded (Level {expansionLevel})</span>
          )}
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

        {/* Interactions Section */}
        {interactions.length > 0 && (
          <div className={styles.interactionsSection}>
            <div className={styles.sectionTitle}>
              Interactions ({interactions.length})
            </div>
            
            {ppiInteractions.length > 0 && (
              <div className={styles.interactionGroup}>
                <div className={styles.groupTitle}>PPI Interactions ({ppiInteractions.length})</div>
                <div className={styles.interactionList}>
                  {ppiInteractions.slice(0, 10).map((edge, idx) => {
                    const connectedNodeId = edge.source === node.id ? edge.target : edge.source;
                    const connectedNode = connectedNodes.get(connectedNodeId);
                    const connectedLabel = connectedNode?.locus_tag || connectedNode?.name || connectedNodeId;
                    
                    return (
                      <div key={idx} className={styles.interactionItem}>
                        <span className={styles.interactionNode}>{connectedLabel}</span>
                        {edge.weight !== undefined && (
                          <span className={styles.interactionScore}>
                            {edge.weight.toFixed(3)}
                          </span>
                        )}
                      </div>
                    );
                  })}
                  {ppiInteractions.length > 10 && (
                    <div className={styles.moreItems}>
                      + {ppiInteractions.length - 10} more...
                    </div>
                  )}
                </div>
              </div>
            )}

            {orthologInteractions.length > 0 && (
              <div className={styles.interactionGroup}>
                <div className={styles.groupTitle}>Ortholog Relationships ({orthologInteractions.length})</div>
                <div className={styles.interactionList}>
                  {orthologInteractions.slice(0, 10).map((edge, idx) => {
                    const connectedNodeId = edge.source === node.id ? edge.target : edge.source;
                    const connectedNode = connectedNodes.get(connectedNodeId);
                    const connectedLabel = connectedNode?.locus_tag || connectedNode?.name || connectedNodeId;
                    
                    return (
                      <div key={idx} className={styles.interactionItem}>
                        <span className={styles.interactionNode}>{connectedLabel}</span>
                        {edge.orthology_type && (
                          <span className={styles.interactionType}>{edge.orthology_type}</span>
                        )}
                      </div>
                    );
                  })}
                  {orthologInteractions.length > 10 && (
                    <div className={styles.moreItems}>
                      + {orthologInteractions.length - 10} more...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {onExpand && (
          <div className={styles.popupFooter}>
            <button
              className={styles.expandButton}
              onClick={handleExpand}
              disabled={!canExpand || isExpanding || isExpanded}
              title={!canExpand 
                ? `Maximum expansion depth reached` 
                : isExpanded 
                ? `Already expanded` 
                : `Show interactions for this node`
              }
            >
              {isExpanding ? 'Loading...' : 'Show Interactions'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

