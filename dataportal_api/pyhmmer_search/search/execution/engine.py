"""Run phmmer against an already loaded set of target sequences."""

from __future__ import annotations

import logging

from pyhmmer.easel import DigitalSequenceBlock
from pyhmmer.plan7 import Builder, Pipeline

from .hits import build_hits
from .schemas import PipelineParameters, QuerySequence
from ..schemas import HitSchema

logger = logging.getLogger(__name__)


def search_targets(
    query: QuerySequence,
    digital_query,
    digital_targets: list,
    target_sequences: dict,
    alphabet,
    parameters: PipelineParameters,
    membership: dict | None,
) -> list[HitSchema]:
    logger.info("Pipeline kwargs: %s", parameters.pipeline_kwargs())
    pipeline = Pipeline(alphabet, **parameters.pipeline_kwargs())
    builder_kwargs = parameters.builder_kwargs()
    logger.info("Builder kwargs: %s", builder_kwargs)
    if parameters.mx:
        logger.info(
            "Scoring matrix requested: %s, but PyHMMER uses its internal scoring system",
            parameters.mx,
        )
    builder = Builder(alphabet, **builder_kwargs)

    block = DigitalSequenceBlock(alphabet)
    block.extend(digital_targets)
    hits = list(pipeline.search_seq(digital_query, block, builder=builder))
    logger.info("PyHMMER returned %s hits", len(hits))
    return build_hits(
        hits,
        query=query,
        target_sequences=target_sequences,
        threshold=parameters.threshold,
        inc_e=parameters.incE,
        inc_t=parameters.incT,
        membership=membership,
    )
