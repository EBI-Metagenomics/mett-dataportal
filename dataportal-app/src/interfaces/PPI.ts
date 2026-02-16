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
  
  // Scores
  dl_score?: number | null;
  comelt_score?: number | null;
  perturbation_score?: number | null;
  abundance_score?: number | null;
  melt_score?: number | null;
  secondary_score?: number | null;
  bayesian_score?: number | null;
  string_score?: number | null;
  operon_score?: number | null;
  ecocyc_score?: number | null;
  tt_score?: number | null;
  ds_score?: number | null;
  
  // Evidence flags
  has_xlms: boolean;
  has_string: boolean;
  has_operon: boolean;
  has_ecocyc: boolean;
  
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
  weight?: number;
  score_type?: string;
  evidence_types?: string[];
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

/** Raw STRING network response shape (simplified, as returned by /ppi/string-network). */
export interface PPIStringNetworkRaw {
  interaction?: any;
  network: Array<Record<string, any>>;
  network_url?: string | null;
  raw_text?: string | null;
  identifiers?: string[];
  species_taxid?: number;
  data_sources?: string[];
  /** When querying by locus_tag, the STRING preferred name of that protein for merging "both" view. */
  focal_preferred_name?: string | null;
  /** Map STRING preferred name -> locus_tag so nodes can be shown by locus tag. */
  preferred_name_to_locus_tag?: Record<string, string>;
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
}

/** Response from /ppi/neighborhood (top N interactors by graph distance). */
export interface PPINeighborhoodData {
  protein_id: string;
  neighbors: Array<{ id: string; label?: string; locus_tag?: string; name?: string; product?: string }>;
  network_data: PPINetworkData;
}

