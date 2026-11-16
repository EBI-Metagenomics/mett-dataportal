import { PPINetworkEdge, PPINetworkNode } from '../../../../../interfaces/PPI';
import { LOCAL_EVIDENCE_CATEGORIES, type LocalEvidenceCategory } from '../constants';

function isLocalPpiEdge(edge: PPINetworkEdge & { dataSource?: string; edgeType?: string }): boolean {
  if (edge.edgeType === 'ortholog') return false;
  const dataSource = edge.dataSource ?? 'local';
  return dataSource === 'local';
}

/** Keep a local edge when at least one selected category supports it. */
export function edgeMatchesLocalEvidence(
  edge: PPINetworkEdge & { dataSource?: string; edgeType?: string },
  selected: readonly LocalEvidenceCategory[],
): boolean {
  if (!isLocalPpiEdge(edge)) return true;
  if (selected.length === LOCAL_EVIDENCE_CATEGORIES.length) return true;
  if (selected.length === 0) return false;

  return selected.some((value) => {
    const category = LOCAL_EVIDENCE_CATEGORIES.find((item) => item.value === value);
    if (!category) return false;
    const count = edge.network_counts?.[category.countField] ?? 0;
    const score = edge.evidence_scores?.[category.scoreField] ?? 0;
    return count > 0 || score > 0;
  });
}

/**
 * Hide local edges that lack the selected evidence categories.
 * STRING and ortholog edges stay. The focal node stays even if it becomes isolated.
 */
export function applyLocalEvidenceFilter<N extends PPINetworkNode>(
  nodes: N[],
  edges: Array<PPINetworkEdge & { dataSource?: string; edgeType?: string }>,
  selected: readonly LocalEvidenceCategory[],
  focalId?: string | null,
): { nodes: N[]; edges: typeof edges } {
  if (selected.length === LOCAL_EVIDENCE_CATEGORIES.length) {
    return { nodes, edges };
  }

  const keptEdges = edges.filter((edge) => edgeMatchesLocalEvidence(edge, selected));
  const ids = new Set<string>();
  keptEdges.forEach((edge) => {
    ids.add(edge.source);
    ids.add(edge.target);
  });

  if (focalId) {
    const focal = nodes.find((node) => node.id === focalId || node.locus_tag === focalId);
    if (focal) ids.add(focal.id);
  }

  return {
    nodes: nodes.filter((node) => ids.has(node.id)),
    edges: keptEdges.filter((edge) => ids.has(edge.source) && ids.has(edge.target)),
  };
}
