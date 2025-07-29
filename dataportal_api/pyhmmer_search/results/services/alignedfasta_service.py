import gzip
import io
import logging
import re
from typing import Any
from typing import Dict, List

from pyhmmer.easel import TextSequence, DigitalSequenceBlock, Alphabet
from pyhmmer.hmmer import hmmalign
from pyhmmer.plan7 import Background, Builder

logger = logging.getLogger(__name__)

VALID_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY*")


class DownloadAlignedFastaService:
    """Service for alignment and MSA processing."""

    @staticmethod
    def generate_enhanced_aligned_fasta_content(
        results: List[Dict[str, Any]], db_path: str, query_input: str
    ) -> bytes:
        logger.info("Generating aligned FASTA content using PyHMMER...")
        return DownloadAlignedFastaService.generate_pyhmmer_msa_content(
            results, db_path, query_input
        )

    @staticmethod
    def generate_pyhmmer_msa_content(
        results: List[Dict[str, Any]], db_path: str, query_input: str
    ) -> bytes:
        from .sequence_service import SequenceService

        target_names = [hit["target"] for hit in results if "target" in hit]
        all_sequences = SequenceService.fetch_sequences_parallel(target_names, db_path)
        return DownloadAlignedFastaService.build_aligned_fasta_msa(
            query_input, results, all_sequences
        )

    @staticmethod
    def clean_sequence(seq: str) -> str:
        cleaned = "".join(char for char in seq if char in VALID_AMINO_ACIDS)
        return cleaned

    @staticmethod
    def build_aligned_fasta_msa(
        query_input: str, hits: List[Dict], all_sequences: Dict[str, str]
    ) -> bytes:
        match = re.match(r"^>(.*$)\n([\s\S]+)", query_input, re.MULTILINE)
        if not match:
            raise ValueError(f"Invalid query input: {query_input}")
        header, input_sequence = match.groups()

        # Clean query input
        input_sequence = DownloadAlignedFastaService.clean_sequence(input_sequence)
        if not input_sequence:
            raise ValueError(
                "Query sequence is empty after removing invalid characters."
            )

        alphabet = Alphabet.amino()
        builder = Builder(alphabet)
        background = Background(alphabet)

        # Build query HMM
        sequence = TextSequence(name=header.encode(), sequence=input_sequence)
        hmm, _, _ = builder.build(sequence.digitize(alphabet), background)

        # Collect digitized domain sequences
        digital_seqs = []
        for hit in hits:
            target = hit.get("target", "")
            if not target or target not in all_sequences:
                continue
            full_seq = all_sequences[target]
            for domain in hit.get("domains", []):
                env_from = domain.get("env_from", 1)
                env_to = domain.get("env_to", len(full_seq))
                raw_subseq = full_seq[env_from - 1 : env_to]
                cleaned_subseq = DownloadAlignedFastaService.clean_sequence(raw_subseq)

                if not cleaned_subseq:
                    logger.warning(
                        f"Skipping sequence for target '{target}' due to invalid characters."
                    )
                    continue

                name = f"{target}/{env_from}-{env_to}".encode()
                try:
                    digitized = TextSequence(
                        name=name, sequence=cleaned_subseq
                    ).digitize(alphabet)
                    digital_seqs.append(digitized)
                except Exception as e:
                    logger.warning(
                        f"Failed to digitize sequence '{name.decode()}': {e}"
                    )

        if not digital_seqs:
            raise ValueError("No valid sequences available for alignment.")

        seq_block = DigitalSequenceBlock(alphabet, digital_seqs)
        msa = hmmalign(hmm, seq_block)

        # Output aligned FASTA
        buf = io.BytesIO()
        for i, aligned_seq in enumerate(msa.alignment):
            name = msa.sequences[i].name.decode()
            buf.write(f">{name}\n".encode())
            for j in range(0, len(aligned_seq), 60):
                buf.write(aligned_seq[j : j + 60].encode() + b"\n")

        return gzip.compress(buf.getvalue())
