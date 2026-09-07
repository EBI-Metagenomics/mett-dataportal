"""Run gene-level experiment ingest into gene_experiment_index."""

from __future__ import annotations

from typing import Optional

from dataportal.ingest.gene_experiment.fitness import Fitness
from dataportal.ingest.gene_experiment.mutant_growth import MutantGrowthFlow
from dataportal.ingest.gene_experiment.pooled_ttp import PooledTTP
from dataportal.ingest.gene_experiment.protein_compound import ProteinCompound
from dataportal.ingest.gene_experiment.proteomics import Proteomics
from dataportal.ingest.gene_experiment.reactions import Reactions
from dataportal.ingest.utils import list_csv_files


def ingest_gene_experiments(
    *,
    experiment_index: str,
    feature_index: str,
    fitness_dir: Optional[str] = None,
    proteomics_dir: Optional[str] = None,
    protein_compound_dir: Optional[str] = None,
    pooled_ttp_dir: Optional[str] = None,
    pool_metadata: Optional[str] = None,
    mutant_growth_dir: Optional[str] = None,
    gene_rx_dir: Optional[str] = None,
    met_rx_dir: Optional[str] = None,
    rx_gpr_dir: Optional[str] = None,
) -> None:
    for csv_path in list_csv_files(fitness_dir):
        Fitness(index_name=experiment_index, feature_flag_index=feature_index).run(csv_path)

    for csv_path in list_csv_files(proteomics_dir):
        Proteomics(index_name=experiment_index, feature_flag_index=feature_index).run(csv_path)

    for csv_path in list_csv_files(protein_compound_dir):
        ProteinCompound(index_name=experiment_index, feature_flag_index=feature_index).run(csv_path)

    for csv_path in list_csv_files(pooled_ttp_dir):
        PooledTTP(
            index_name=experiment_index,
            pool_metadata_path=pool_metadata,
            feature_flag_index=feature_index,
        ).run(csv_path)

    gene_rx_files = list_csv_files(gene_rx_dir)
    met_rx_files = list_csv_files(met_rx_dir)
    rx_gpr_files = list_csv_files(rx_gpr_dir)
    for gr in gene_rx_files:
        for mr in met_rx_files:
            for gp in rx_gpr_files:
                Reactions(index_name=experiment_index, feature_flag_index=feature_index).run(
                    gr, mr, gp
                )

    for csv_path in list_csv_files(mutant_growth_dir):
        MutantGrowthFlow(index_name=experiment_index, feature_flag_index=feature_index).run(
            csv_path
        )
