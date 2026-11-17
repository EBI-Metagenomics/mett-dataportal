import { BaseService } from '../common/BaseService';

export interface PPIPathNode {
  id: string;
  locus_tag?: string | null;
  name?: string | null;
  product?: string | null;
  role: 'seed' | 'intermediate';
}

export interface PPIPathEdge {
  source: string;
  target: string;
  weight?: number | null;
  pair_id?: string | null;
  consensus_score?: number | null;
  raw_consensus_score?: number | null;
  n_evidence_types?: number | null;
  n_networks_total?: number | null;
  evidence_scores?: Record<string, number> | null;
  network_counts?: Record<string, number> | null;
}

export interface PPIDisconnectedPair {
  locus_tag_a: string;
  locus_tag_b: string;
}

export interface PPIPathsResult {
  seeds: PPIPathNode[];
  intermediates: PPIPathNode[];
  edges: PPIPathEdge[];
  paths: Array<{ locus_tags: string[]; protein_ids: string[] }>;
  disconnected_pairs: PPIDisconnectedPair[];
}

export interface PPIPathsRequest {
  locus_tags: string[];
  species_acronym?: string;
  score_type: string;
  score_threshold: number;
}

/** HTTP client for POST /ppi/paths. Neighborhood calls stay on PPIService. */
export class PPIPathService extends BaseService {
  static async findPaths(request: PPIPathsRequest): Promise<PPIPathsResult> {
    return this.postWithRetry<PPIPathsResult>('/ppi/paths', {
      locus_tags: request.locus_tags,
      species_acronym: request.species_acronym,
      score_type: request.score_type,
      score_threshold: request.score_threshold,
    });
  }
}
