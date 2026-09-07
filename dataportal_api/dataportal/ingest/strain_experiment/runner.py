"""Run strain-level experiment ingest into strain_experiment_index."""

from __future__ import annotations

from typing import Optional

from dataportal.ingest.es_repo import StrainExperimentIndexRepository, StrainIndexRepository
from dataportal.ingest.strain.resolver import StrainResolver
from dataportal.ingest.strain_experiment.importers import DrugMetabolismUpserter, DrugMICUpserter


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
