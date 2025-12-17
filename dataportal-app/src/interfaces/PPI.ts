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

export interface PPINetworkNode {
  id: string;
  label?: string;
  locus_tag?: string;
  name?: string;
  product?: string;
  uniprot_id?: string;
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

