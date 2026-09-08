"""Run gene-level experiment ingest into gene_experiment_index."""

from __future__ import annotations

from typing import Optional

from elasticsearch_dsl.connections import connections

from dataportal.ingest.gene_experiment.fitness import Fitness
from dataportal.ingest.gene_experiment.mutant_growth import MutantGrowthFlow
from dataportal.ingest.gene_experiment.pooled_ttp import PooledTTP
from dataportal.ingest.gene_experiment.protein_compound import ProteinCompound
from dataportal.ingest.gene_experiment.proteomics import Proteomics
from dataportal.ingest.gene_experiment.reactions import Reactions
from dataportal.ingest.utils import list_csv_files


def _describe_index(name: str) -> str:
    try:
        resolved = connections.get_connection().indices.resolve_index(name=name)
        if hasattr(resolved, "body"):
            resolved = resolved.body
        elif not isinstance(resolved, dict):
            resolved = dict(resolved)
        concrete = []
        for idx in resolved.get("indices", []) or []:
            if isinstance(idx, dict):
                concrete.append(idx.get("name") or "")
        for alias in resolved.get("aliases", []) or []:
            if isinstance(alias, dict):
                concrete.extend(alias.get("indices") or [])
        concrete = [c for c in concrete if c]
        if concrete and set(concrete) != {name}:
            return f"{name} -> {', '.join(sorted(set(concrete)))}"
    except Exception:
        pass
    return name


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
    print(
        f"[import_gene_experiments] Writing assays to {_describe_index(experiment_index)}; "
        f"stamping has_* flags on {_describe_index(feature_index)}"
    )
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
