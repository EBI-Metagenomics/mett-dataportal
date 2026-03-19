import React, { useMemo } from 'react';
import type { PPINetworkNode } from '../../../../../interfaces/PPI';
import styles from './SourceOverlapDebug.module.scss';

interface SourceOverlapDebugProps {
  localNodes: PPINetworkNode[];
  stringNodes: PPINetworkNode[];
}

/**
 * Computes canonical identifier for overlap: prefer locus_tag (matches across sources),
 * fallback to id (local may use UniProt, STRING may use locus_tag or STRING id).
 */
function canonicalId(node: PPINetworkNode): string {
  return (node.locus_tag ?? node.id ?? '').trim() || node.id;
}

export const SourceOverlapDebug: React.FC<SourceOverlapDebugProps> = ({
  localNodes,
  stringNodes,
}) => {
  const stats = useMemo(() => {
    const localIds = new Set(localNodes.map(canonicalId).filter(Boolean));
    const stringIds = new Set(stringNodes.map(canonicalId).filter(Boolean));
    const overlap = new Set([...localIds].filter((id) => stringIds.has(id)));
    const localOnly = [...localIds].filter((id) => !stringIds.has(id));
    const stringOnly = [...stringIds].filter((id) => !localIds.has(id));
    return {
      localCount: localIds.size,
      stringCount: stringIds.size,
      overlapCount: overlap.size,
      localOnly,
      stringOnly,
    };
  }, [localNodes, stringNodes]);

  return (
    <details className={styles.overlapDebug}>
      <summary>Source overlap (Local vs STRING)</summary>
      <div className={styles.stats}>
        <div className={styles.row}>
          <span>Local nodes:</span>
          <strong>{stats.localCount}</strong>
        </div>
        <div className={styles.row}>
          <span>STRING nodes:</span>
          <strong>{stats.stringCount}</strong>
        </div>
        <div className={styles.row}>
          <span>Overlap (same locus_tag/id):</span>
          <strong>{stats.overlapCount}</strong>
        </div>
        <div className={styles.row}>
          <span>Local only:</span>
          <strong>{stats.localOnly.length}</strong>
          {stats.localOnly.length > 0 && (
            <code className={styles.sample} title={stats.localOnly.join(', ')}>
              {stats.localOnly.slice(0, 3).join(', ')}
              {stats.localOnly.length > 3 ? ` +${stats.localOnly.length - 3} more` : ''}
            </code>
          )}
        </div>
        <div className={styles.row}>
          <span>STRING only:</span>
          <strong>{stats.stringOnly.length}</strong>
          {stats.stringOnly.length > 0 && (
            <code className={styles.sample} title={stats.stringOnly.join(', ')}>
              {stats.stringOnly.slice(0, 3).join(', ')}
              {stats.stringOnly.length > 3 ? ` +${stats.stringOnly.length - 3} more` : ''}
            </code>
          )}
        </div>
        <div className={styles.row}>
          <span>Local ID sample:</span>
          <code className={styles.sample} title={localNodes.slice(0, 10).map((n) => `id: ${n.id}${n.locus_tag ? ` | locus_tag: ${n.locus_tag}` : ''}`).join('\n')}>
            {localNodes.slice(0, 3).map((n) => n.id).join(', ')}
            {localNodes.length > 3 ? ' …' : ''}
          </code>
        </div>
        <div className={styles.row}>
          <span>STRING ID sample:</span>
          <code className={styles.sample} title={stringNodes.slice(0, 10).map((n) => `id: ${n.id}${n.locus_tag ? ` | locus_tag: ${n.locus_tag}` : ''}`).join('\n')}>
            {stringNodes.slice(0, 3).map((n) => n.id).join(', ')}
            {stringNodes.length > 3 ? ' …' : ''}
          </code>
        </div>
      </div>
      <p className={styles.hint}>
        Low overlap can mean: different scoring/filters, ID mismatches (UniProt vs locus_tag),
        or STRING/local use different interaction data. Hover for locus_tag/id details.
      </p>
    </details>
  );
};
