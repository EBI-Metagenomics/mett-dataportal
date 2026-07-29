import React, { useEffect, useState } from 'react';
import { PPINetworkNode, PPINetworkEdge, StringScoreBreakdown } from '../../../../../interfaces/PPI';
import { GeneService } from '../../../../../services/gene/geneService';
import { STRING_SCORE_LABELS } from '../constants';
import { canExpandNode, getNodeExpansionLevel } from '../utils/expansionUtils';
import { ExpansionState } from '../types/expansion';
import { useClampPopupToViewport } from '../utils/useClampPopupToViewport';
import { getNodeDisplayLabel } from '../NetworkGraph/utils/prepareElements';
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

const hasText = (value?: string | null): value is string =>
  typeof value === 'string' && value.trim().length > 0;

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
  const [enrichedNode, setEnrichedNode] = useState<PPINetworkNode>(node);

  useEffect(() => {
    setEnrichedNode(node);
  }, [node]);

  // Fill missing name/product from feature index when PPI payload is incomplete
  // (common for Top-N focal nodes before backend fix, or genes without GFF Name).
  useEffect(() => {
    const locusTag = node.locus_tag?.trim();
    if (!locusTag) return;
    if (hasText(node.name) && hasText(node.product)) return;

    let cancelled = false;
    (async () => {
      try {
        const gene = await GeneService.fetchGeneByLocusTag(locusTag);
        if (cancelled || !gene) return;
        setEnrichedNode((prev) => ({
          ...prev,
          name: hasText(prev.name) ? prev.name : (gene.gene_name || gene.uf_gene_name || undefined),
          product: hasText(prev.product) ? prev.product : (gene.product || undefined),
          uniprot_id: prev.uniprot_id || gene.uniprot_id || undefined,
        }));
      } catch (err) {
        console.warn('Failed to enrich node popup from gene API:', err);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [node]);

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

  const { popupRef, shift } = useClampPopupToViewport(x, y);
  const title = getNodeDisplayLabel(enrichedNode);
  const showLocusUnderTitle =
    hasText(enrichedNode.locus_tag) &&
    enrichedNode.locus_tag !== title;

  return (
    <div className={styles.popupOverlay} onClick={onClose}>
      <div
        ref={popupRef}
        className={styles.popupContent}
        onClick={(e) => e.stopPropagation()}
        style={{
          left: `${x + shift.dx}px`,
          top: `${y + shift.dy}px`,
        }}
      >
        <div className={styles.popupHeader}>
          <div className={styles.popupHeaderText}>
            <h3>{title}</h3>
            {showLocusUnderTitle && (
              <div className={styles.subtitle}>{enrichedNode.locus_tag}</div>
            )}
            {isExpanded && (
              <span className={styles.expandedBadge}>Expanded (Level {expansionLevel})</span>
            )}
          </div>
          <button type="button" className={styles.closeButton} onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className={styles.popupScroll}>
        <div className={styles.popupBody}>
          {hasText(enrichedNode.name) && (
            <div className={styles.infoRow}>
              <span className={styles.label}>Name:</span>
              <span className={styles.value}>{enrichedNode.name}</span>
            </div>
          )}
          {hasText(enrichedNode.product) && (
            <div className={styles.infoRow}>
              <span className={styles.label}>Product:</span>
              <span className={styles.value}>{enrichedNode.product}</span>
            </div>
          )}
          {(enrichedNode.uniprot_id || enrichedNode.id) && (
            <div className={styles.infoRow}>
              <span className={styles.label}>UniProt ID:</span>
              <span className={styles.value}>{enrichedNode.uniprot_id || enrichedNode.id}</span>
            </div>
          )}
          {hasText(enrichedNode.locus_tag) && (
            <div className={styles.infoRow}>
              <span className={styles.label}>Locus Tag:</span>
              <span className={styles.value}>{enrichedNode.locus_tag}</span>
            </div>
          )}

          {/* STRING DB section: show when node has STRING API data */}
          {(enrichedNode.string_id || enrichedNode.string_preferred_name) && (
            <div className={styles.stringSection}>
              <div className={styles.sectionTitle}>STRING DB</div>
              {enrichedNode.string_id && (
                <div className={styles.infoRow}>
                  <span className={styles.label}>STRING protein ID:</span>
                  <span className={styles.value}>{enrichedNode.string_id}</span>
                </div>
              )}
              {enrichedNode.string_preferred_name && (
                <div className={styles.infoRow}>
                  <span className={styles.label}>Preferred name:</span>
                  <span className={styles.value}>{enrichedNode.string_preferred_name}</span>
                </div>
              )}
              {!enrichedNode.locus_tag && (enrichedNode.string_id || enrichedNode.string_preferred_name) && (
                <div className={styles.infoRow}>
                  <span className={styles.label}>Locus tag:</span>
                  <span className={styles.valueMuted}>Not in feature index mapping</span>
                </div>
              )}
              {enrichedNode.string_score_breakdown && (
                <div className={styles.scoreBreakdown}>
                  <div className={styles.groupTitle}>Score breakdown (from STRING)</div>
                  {(Object.keys(STRING_SCORE_LABELS) as (keyof StringScoreBreakdown)[]).map((key) => {
                    const val = enrichedNode.string_score_breakdown![key];
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
                    const connectedLabel = connectedNode
                      ? getNodeDisplayLabel(connectedNode)
                      : connectedNodeId;
                    
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
                    const connectedLabel = connectedNode
                      ? getNodeDisplayLabel(connectedNode)
                      : connectedNodeId;
                    
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
        </div>

        {((onViewInJBrowse && !isOrthologNode && enrichedNode.locus_tag) || (onExpand && !isOrthologNode)) && (
          <div className={styles.popupFooter}>
            {onViewInJBrowse && !isOrthologNode && enrichedNode.locus_tag && (
              <button
                type="button"
                className={styles.viewInJBrowseButton}
                onClick={() => {
                  onClose();
                  onViewInJBrowse(enrichedNode.locus_tag!);
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
