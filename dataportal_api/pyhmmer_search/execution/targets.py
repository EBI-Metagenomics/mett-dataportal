"""Load the subset of the protein FASTA selected by a search scope."""

from __future__ import annotations

import logging

from pyhmmer.easel import SequenceFile

logger = logging.getLogger(__name__)


def load_targets(db_path: str, alphabet, membership: dict | None):
    """Digitize sequences whose representative id is in ``membership``.

    ``membership is None`` means the index is missing, so every sequence is loaded.
    """
    wanted = set(membership) if membership is not None else None
    digital_targets = []
    target_sequences = {}
    with SequenceFile(db_path, format="fasta") as target_file:
        for seq in target_file:
            seq_name = seq.name.decode()
            if wanted is not None and seq_name not in wanted:
                continue
            target_sequences[seq_name] = seq
            digital_targets.append(seq.digitize(alphabet))
    logger.info("Digitized %s target sequences from %s", len(digital_targets), db_path)
    return digital_targets, target_sequences
