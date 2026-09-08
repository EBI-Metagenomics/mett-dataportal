"""
Elasticsearch ingest, grouped by write target (not by CSV source type).

Packages:
  species              species_index
  strain               strain_index (isolate identity, contigs)
  strain_experiment    strain_experiment_index (MIC, metabolism, later strain assays)
  feature              feature_index (GFF, essentiality, STRING dbxref)
  gene_experiment      gene_experiment_index (fitness, proteomics, TPP, reactions, mutant growth)
  fitness_correlation  fitness_correlation_index
  ppi / ortholog / operon
  gff                  shared GFF parser used by interaction ingest
"""
