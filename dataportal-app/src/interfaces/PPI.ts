/**
 * Interfaces for Protein-Protein Interaction (PPI) data structures
 */

export interface PPIInteraction {
  pair_id: string;
  species_scientific_name?: string | null;
  species_acronym?: string | null;
  isolate_name?: string | null;
  protein_a: string;
  protein_b: string;
  participants: string[];
  is_self_interaction: boolean;
  
  // Gene information for protein_a
  protein_a_locus_tag?: string | null;
  protein_a_uniprot_id?: string | null;
  protein_a_name?: string | null;
  protein_a_product?: string | null;
  
  // Gene information for protein_b
  protein_b_locus_tag?: string | null;
  protein_b_uniprot_id?: string | null;
  protein_b_name?: string | null;
  protein_b_product?: string | null;
  
  // PPI v4 consensus and evidence-category scores
  consensus_score?: number | null;
  raw_consensus_score?: number | null;
  consensus_rank?: number | null;
  edge_id?: string | null;
  q_ppi?: number | null;
  q_chemical_genetic?: number | null;
  q_coexpression?: number | null;
  q_operons?: number | null;
  q_metabolic?: number | null;

  // Supporting network counts
  n_evidence_types?: number | null;
  n_networks_total?: number | null;
  n_ppi?: number | null;
  n_chemical_genetic?: number | null;
  n_coexpression?: number | null;
  n_operons?: number | null;
  n_metabolic?: number | null;

  // Evidence-category presence
  has_ppi: boolean;
  has_chemical_genetic: boolean;
  has_coexpression: boolean;
  has_operons: boolean;
  has_metabolic: boolean;
  
  // Metadata
  evidence_count: number;
}

/** STRING DB score breakdown from network row (one row = one interaction). */
export interface StringScoreBreakdown {
  score?: number | string;
  nscore?: number | string;
  fscore?: number | string;
  pscore?: number | string;
  ascore?: number | string;
  escore?: number | string;
  dscore?: number | string;
  tscore?: number | string;
  ncbiTaxonId?: number | string;
}

/** Non-zero evidence-category scores from the local PPI v4 network. */
export type LocalEvidenceScores = Record<string, number>;

/** Non-zero per-category network counts (n_ppi, n_operons, and so on). */
export type LocalNetworkCounts = Record<string, number>;

export interface PPINetworkNode {
  id: string;
  label?: string;
  locus_tag?: string;
  name?: string;
  product?: string;
  uniprot_id?: string;
  /** STRING protein ID (e.g. 820.ERS852554_00297) when node comes from STRING DB. */
  string_id?: string;
  /** STRING preferred name (e.g. dnaN_1) when node comes from STRING DB. */
  string_preferred_name?: string;
  /** Score breakdown from STRING network row (neighborhood, fusion, coexpression, etc.). */
  string_score_breakdown?: StringScoreBreakdown;
  [key: string]: any;
}

export interface PPINetworkEdge {
  source: string;
  target: string;
  /** Edge weight shown on the graph (selected score, default consensus_score). */
  weight?: number;
  score_type?: string;
  /** Canonical interaction pair ID for detail lookups. */
  pair_id?: string;
  consensus_score?: number;
  raw_consensus_score?: number;
  /** Number of evidence categories supporting the interaction. */
  n_evidence_types?: number;
  /** Total supporting networks across categories. */
  n_networks_total?: number;
  evidence_types?: string[];
  /** Non-zero evidence-category scores for the interaction details panel. */
  evidence_scores?: LocalEvidenceScores;
  /** Non-zero per-category network counts. */
  network_counts?: LocalNetworkCounts;
  [key: string]: any;
}

export interface PPINetworkProperties {
  num_nodes: number;
  num_edges: number;
  density: number;
  avg_clustering_coefficient: number;
  degree_distribution: number[];
  internal_only_edges?: number;
  cross_species_edges?: number;
  avg_degree?: number;
  ppi_enrichment_p_value?: number;
}

export interface PPINetworkData {
  nodes: PPINetworkNode[];
  edges: PPINetworkEdge[];
  properties?: PPINetworkProperties;
}

/** Logical identifiers for PPI data sources used in the UI. */
export type PPIDataSource = 'local' | 'stringdb' | 'both';

/** Available PPI data sources response (from /ppi/data-sources). */
export interface PPIDataSources {
  sources: string[];
  default: string | null;
}

/** Raw STRING network response shape (from /ppi/string-network). */
export interface PPIStringNetworkRaw {
  interaction?: any;
  network: Array<Record<string, any>>;
  network_url?: string | null;
  raw_text?: string | null;
  identifiers?: string[];
  species_taxid?: number;
  data_sources?: string[];
  /** Queried locus tag (when locus_tag was provided). */
  focal_locus_tag?: string | null;
  /** STRING preferred name for the focal protein (for merging "both" view). */
  focal_preferred_name?: string | null;
  /** STRING protein ID of the focal gene. */
  focal_string_id?: string | null;
  /** Number of edges removed (unmapped locus tags). Present when filtering occurred. */
  edges_filtered_unmapped?: number;
  /** STRING IDs with no locus tag mapping. Present when filtering occurred. */
  unmapped_string_ids?: string[];
  error?: string | null;
}

export interface PPINetworkQuery {
  score_type: string;
  score_threshold: number;
  species_acronym?: string;
  isolate_name?: string;
  locus_tag?: string; // Optional: Filter to PPIs involving this locus_tag
  include_properties?: boolean;
}

export interface PPIScoreType {
  score_types: string[];
  default?: string;
  evidence_channels?: Record<string, string>;
}

/** Response from /ppi/neighborhood (top N interactors by graph distance). */
export interface PPINeighborhoodData {
  protein_id: string;
  neighbors: Array<{ id: string; label?: string; locus_tag?: string; name?: string; product?: string }>;
  network_data: PPINetworkData;
}
