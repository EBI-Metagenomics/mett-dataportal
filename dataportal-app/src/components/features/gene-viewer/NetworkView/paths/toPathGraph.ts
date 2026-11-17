import { PPINetworkEdge, PPINetworkNode } from '../../../../../interfaces/PPI';
import { PPIPathNode, PPIPathsResult } from '../../../../../services/interactions/ppiPathService';

export interface PathGraph {
  nodes: Array<PPINetworkNode & { pathRole: 'seed' | 'intermediate'; nodeType: 'ppi' }>;
  edges: PPINetworkEdge[];
}

export function shouldReplaceNetwork(result: { edges: unknown[] }): boolean {
  return result.edges.length > 0;
}

function toNode(node: PPIPathNode): PathGraph['nodes'][number] {
  const locus = node.locus_tag?.trim() || undefined;
  return {
    id: node.id,
    locus_tag: locus,
    name: node.name || undefined,
    product: node.product || undefined,
    label: locus || node.name || node.id,
    pathRole: node.role,
    nodeType: 'ppi',
  };
}

/** Map a path response onto the nodes and edges the network graph already draws. */
export function toPathGraph(result: PPIPathsResult): PathGraph {
  return {
    nodes: [...result.seeds, ...result.intermediates].map(toNode),
    edges: result.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      weight: edge.weight ?? undefined,
      pair_id: edge.pair_id ?? undefined,
      consensus_score: edge.consensus_score ?? undefined,
      raw_consensus_score: edge.raw_consensus_score ?? undefined,
      n_evidence_types: edge.n_evidence_types ?? undefined,
      n_networks_total: edge.n_networks_total ?? undefined,
      evidence_scores: edge.evidence_scores ?? undefined,
      network_counts: edge.network_counts ?? undefined,
      dataSource: 'local',
      edgeType: 'ppi',
    })),
  };
}

export function disconnectedPairLabels(result: PPIPathsResult): string[] {
  return result.disconnected_pairs.map((pair) => `${pair.locus_tag_a} — ${pair.locus_tag_b}`);
}
