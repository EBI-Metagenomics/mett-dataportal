/**
 * Interfaces for Ortholog data structures
 */

export interface OrthologRelationship {
  locus_tag_a: string;
  locus_tag_b: string;
  species_acronym_a?: string;
  species_acronym_b?: string;
  orthology_type?: string; // '1:1', 'many:1', '1:many', 'many:many'
  confidence_score?: number;
}

export interface GeneOrthologs {
  locus_tag: string;
  orthologs: OrthologRelationship[];
  total_count: number;
}

