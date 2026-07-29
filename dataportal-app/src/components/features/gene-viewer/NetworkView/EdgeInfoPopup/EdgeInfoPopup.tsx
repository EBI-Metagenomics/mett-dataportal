import React, { useMemo } from 'react';
import { LocalEvidenceScores, PPINetworkEdge, StringScoreBreakdown } from '../../../../../interfaces/PPI';
import {
  EVIDENCE_DISPLAY_LABELS,
  LOCAL_EVIDENCE_CHANNEL_LABELS,
  STRING_EVIDENCE_CHANNELS,
  STRING_EVIDENCE_SCORE_FIELDS,
} from '../constants';
import { useClampPopupToViewport } from '../utils/useClampPopupToViewport';
import styles from './EdgeInfoPopup.module.scss';

interface EdgeInfoPopupProps {
  edge: PPINetworkEdge & {
    edgeType?: string;
    orthology_type?: string;
    expansionLevel?: number;
    string_score_breakdown?: StringScoreBreakdown;
    evidence_scores?: LocalEvidenceScores;
  };
  sourceNode?: { locus_tag?: string; name?: string; product?: string };
  targetNode?: { locus_tag?: string; name?: string; product?: string };
  x: number;
  y: number;
  onClose: () => void;
}

function formatScoreLabel(field: string): string {
  return (
    LOCAL_EVIDENCE_CHANNEL_LABELS[field] ||
    field.replace(/_score$/, '').replace(/^weight_/, '').replace(/_/g, ' ')
  );
}

export const EdgeInfoPopup: React.FC<EdgeInfoPopupProps> = ({
  edge,
  sourceNode,
  targetNode,
  x,
  y,
  onClose,
}) => {
  /** Local consensus evidence channels (from ES network edges). */
  const localEvidenceScores = useMemo(() => {
    const scores = edge.evidence_scores;
    if (!scores || typeof scores !== 'object') return [];
    return Object.entries(scores)
      .filter(([, value]) => typeof value === 'number' && !Number.isNaN(value) && value !== 0)
      .map(([field, score]) => ({
        field,
        label: formatScoreLabel(field),
        score: score as number,
      }))
      .sort((a, b) => b.score - a.score);
  }, [edge]);

  /** For STRING edges with string_score_breakdown, collect all evidence scores > 0 */
  const stringEvidenceScores = useMemo(() => {
    const breakdown = (edge as { string_score_breakdown?: StringScoreBreakdown }).string_score_breakdown;
    if (!breakdown) return [];
    const entries: { label: string; score: number }[] = [];
    STRING_EVIDENCE_CHANNELS.forEach(({ value, label }) => {
      const field = STRING_EVIDENCE_SCORE_FIELDS[value];
      const raw = (breakdown as Record<string, number | string | undefined>)[field];
      if (raw == null) return;
      const num = typeof raw === 'string' ? parseFloat(raw) : raw;
      if (typeof num === 'number' && !Number.isNaN(num) && num > 0) {
        const displayLabel = EVIDENCE_DISPLAY_LABELS[value] ?? label;
        const normalized = num > 1 ? num / 1000 : num;
        entries.push({ label: displayLabel, score: normalized });
      }
    });
    return entries;
  }, [edge]);

  const getEdgeTypeLabel = () => {
    if (edge.edgeType === 'ortholog') {
      return `Ortholog Relationship${edge.orthology_type ? ` (${edge.orthology_type})` : ''}`;
    }
    const evidenceType = (edge as { evidence_type?: string }).evidence_type;
    if (evidenceType) {
      return `STRING: ${evidenceType}`;
    }
    if (localEvidenceScores.length > 0) {
      return 'Consensus Interaction';
    }
    return 'PPI Interaction';
  };

  const scoreTypeLabel = edge.score_type
    ? formatScoreLabel(edge.score_type)
    : localEvidenceScores.length > 0
      ? 'Consensus'
      : null;

  const { popupRef, shift } = useClampPopupToViewport(x, y);

  return (
    <div className={styles.popupOverlay} onClick={onClose}>
      <div
        ref={popupRef}
        className={styles.popupContent}
        onClick={(e) => e.stopPropagation()}
        style={{ left: `${x + shift.dx}px`, top: `${y + shift.dy}px` }}
      >
        <div className={styles.popupHeader}>
          <div className={styles.popupHeaderText}>
            <h3>{getEdgeTypeLabel()}</h3>
            {edge.expansionLevel !== undefined && edge.expansionLevel > 0 && (
              <span className={styles.expansionBadge}>Level {edge.expansionLevel}</span>
            )}
          </div>
          <button type="button" className={styles.closeButton} onClick={onClose} aria-label="Close">
            ×
          </button>
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
            {edge.weight !== undefined && edge.weight !== null && (
              <div className={styles.infoRow}>
                <span className={styles.label}>
                  {scoreTypeLabel ? `${scoreTypeLabel} score:` : 'Score/Weight:'}
                </span>
                <span className={styles.value}>{Number(edge.weight).toFixed(4)}</span>
              </div>
            )}
            {edge.n_sources != null && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Evidence sources:</span>
                <span className={styles.value}>{edge.n_sources}</span>
              </div>
            )}
            {edge.score_type && localEvidenceScores.length === 0 && stringEvidenceScores.length === 0 && (
              <div className={styles.infoRow}>
                <span className={styles.label}>Score Type:</span>
                <span className={styles.value}>{edge.score_type}</span>
              </div>
            )}

            {localEvidenceScores.length > 0 && (
              <>
                <div className={styles.sectionTitle}>Evidence channels</div>
                {localEvidenceScores.map(({ field, label, score }) => (
                  <div key={field} className={styles.infoRow}>
                    <span className={styles.label}>{label}:</span>
                    <span className={styles.value}>{score.toFixed(4)}</span>
                  </div>
                ))}
              </>
            )}

            {stringEvidenceScores.length > 0 && (
              <>
                <div className={styles.sectionTitle}>STRING evidence scores</div>
                {stringEvidenceScores.map(({ label, score }) => (
                  <div key={label} className={styles.infoRow}>
                    <span className={styles.label}>{label}:</span>
                    <span className={styles.value}>{score.toFixed(4)}</span>
                  </div>
                ))}
              </>
            )}

            {localEvidenceScores.length === 0 &&
              stringEvidenceScores.length === 0 &&
              (edge as { evidence_type?: string }).evidence_type && (
                <div className={styles.infoRow}>
                  <span className={styles.label}>Evidence Type:</span>
                  <span className={styles.value}>
                    {(edge as { evidence_type?: string }).evidence_type}
                  </span>
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
