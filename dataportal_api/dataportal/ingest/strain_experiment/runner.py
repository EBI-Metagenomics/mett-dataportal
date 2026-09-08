"""Run strain-level experiment ingest into strain_experiment_index."""

from __future__ import annotations

import logging
from typing import Optional

from dataportal.ingest.es_repo import StrainExperimentIndexRepository, StrainIndexRepository
from dataportal.ingest.strain.resolver import StrainResolver
from dataportal.ingest.strain_experiment.importers import DrugMetabolismUpserter, DrugMICUpserter

logger = logging.getLogger(__name__)


def ingest_strain_experiments(
    *,
    strain_index: str,
    experiment_index: str,
    include_mic: bool = False,
    mic_bu_file: Optional[str] = None,
    mic_pv_file: Optional[str] = None,
    include_metabolism: bool = False,
    metab_bu_file: Optional[str] = None,
    metab_pv_file: Optional[str] = None,
) -> None:
    strain_repo = StrainIndexRepository(concrete_index=strain_index)
    experiment_repo = StrainExperimentIndexRepository(concrete_index=experiment_index)
    resolver = StrainResolver(index=strain_index)
    resolver.load()
    logger.info(
        "Resolving isolate names against %s (%s document(s)); writing to %s",
        strain_index,
        resolver.loaded_count,
        experiment_index,
    )
    print(
        f"[import_strain_experiments] Loaded {resolver.loaded_count} strain(s) from {strain_index}. "
        f"Experiment docs are created only for isolates that exist there and appear in the CSVs."
    )
    if resolver.loaded_count == 0:
        raise RuntimeError(
            f"No strains loaded from '{strain_index}'. "
            "Pass the concrete strain index (or alias) that contains all isolates."
        )

    if include_mic:
        DrugMICUpserter(
            repo=experiment_repo,
            resolver=resolver,
            strain_repo=strain_repo,
            bu_csv=mic_bu_file,
            pv_csv=mic_pv_file,
        ).run()

    if include_metabolism:
        DrugMetabolismUpserter(
            repo=experiment_repo,
            resolver=resolver,
            strain_repo=strain_repo,
            bu_csv=metab_bu_file,
            pv_csv=metab_pv_file,
        ).run()
