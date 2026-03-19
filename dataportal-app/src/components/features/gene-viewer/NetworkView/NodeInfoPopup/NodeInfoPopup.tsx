import React from 'react';
import { PPINetworkNode, PPINetworkEdge, StringScoreBreakdown } from '../../../../../interfaces/PPI';
import { STRING_SCORE_LABELS } from '../constants';
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
  /** When true, hide "Show Interactions" (ortholog nodes don't have PPI expansion in this genome). */
  isOrthologNode?: boolean;
  onClose: () => void;
  onExpand?: (node: PPINetworkNode) => void;
  isExpanding?: boolean;
  /** Navigate JBrowse to this gene (current genome). Only shown for non-ortholog nodes. */
  onViewInJBrowse?: (locusTag: string) => void;
}

export const NodeInfoPopup: React.FC<NodeInfoPopupProps> = ({ 
  node, 
  x, 
  y, 
  expansionState,
  interactions = [],
  connectedNodes = new Map(),
  isOrthologNode = false,
  onClose, 
  onExpand,
  isExpanding = false,
  onViewInJBrowse,
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

          {/* STRING DB section: show when node has STRING API data */}
          {(node.string_id || node.string_preferred_name) && (
            <div className={styles.stringSection}>
              <div className={styles.sectionTitle}>STRING DB</div>
              {node.string_id && (
                <div className={styles.infoRow}>
                  <span className={styles.label}>STRING protein ID:</span>
                  <span className={styles.value}>{node.string_id}</span>
                </div>
              )}
              {node.string_preferred_name && (
                <div className={styles.infoRow}>
                  <span className={styles.label}>Preferred name:</span>
                  <span className={styles.value}>{node.string_preferred_name}</span>
                </div>
              )}
              {!node.locus_tag && (node.string_id || node.string_preferred_name) && (
                <div className={styles.infoRow}>
                  <span className={styles.label}>Locus tag:</span>
                  <span className={styles.valueMuted}>Not in feature index mapping</span>
                </div>
              )}
              {node.string_score_breakdown && (
                <div className={styles.scoreBreakdown}>
                  <div className={styles.groupTitle}>Score breakdown (from STRING)</div>
                  {(Object.keys(STRING_SCORE_LABELS) as (keyof StringScoreBreakdown)[]).map((key) => {
                    const val = node.string_score_breakdown![key];
                    if (val === undefined || val === null || val === '') return null;
                    const num = typeof val === 'string' ? parseFloat(val) : val;
                    const display = typeof num === 'number' && !Number.isNaN(num) ? num.toFixed(3) : String(val);
                    return (
                      <div key={key} className={styles.infoRow}>
                        <span className={styles.label}>{STRING_SCORE_LABELS[key]}:</span>
                        <span className={styles.value}>{display}</span>
                      </div>
                    );
                  })}
                </div>
              )}
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

        {((onViewInJBrowse && !isOrthologNode && node.locus_tag) || (onExpand && !isOrthologNode)) && (
          <div className={styles.popupFooter}>
            {onViewInJBrowse && !isOrthologNode && node.locus_tag && (
              <button
                type="button"
                className={styles.viewInJBrowseButton}
                onClick={() => {
                  onClose();
                  onViewInJBrowse(node.locus_tag!);
                }}
                title="Scroll JBrowse viewer to show this gene"
              >
                View in JBrowse
              </button>
            )}
            {onExpand && !isOrthologNode && (
              <button
                type="button"
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
            )}
          </div>
        )}
      </div>
    </div>
  );
};

