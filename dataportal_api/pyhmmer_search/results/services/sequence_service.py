"""
Sequence service for PyHMMER sequence database operations.
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

from pyhmmer.easel import SequenceFile, SSIReader

logger = logging.getLogger(__name__)


class SequenceService:
    """Service for sequence database operations."""

    @staticmethod
    def fetch_sequence_from_database(target_name: str, db_path: str) -> str:
        """Fetch a single sequence from the database."""
        try:
            from pyhmmer.easel import SequenceFile, SSIReader

            ssi_path = f"{db_path}.ssi"
            if os.path.exists(ssi_path):
                with SSIReader(ssi_path) as ssi_reader:
                    try:
                        key = ssi_reader.find_key(target_name.encode())
                        if key:
                            with SequenceFile(db_path, digital=True) as seqfile:
                                seqfile.select(key)
                                sequence = next(seqfile)
                                # Convert digital sequence to text format
                                return sequence.textize().sequence
                    except Exception as e:
                        logger.debug(f"SSI lookup failed for {target_name}: {e}")

            # Fallback: scan through the file
            with SequenceFile(db_path, digital=True) as seqfile:
                for sequence in seqfile:
                    if sequence.name.decode() == target_name:
                        # Convert digital sequence to text format
                        return sequence.textize().sequence

            logger.warning(f"Sequence not found for target: {target_name}")
            return ""

        except Exception as e:
            logger.error(f"Error fetching sequence for {target_name}: {e}")
            return ""

    @staticmethod
    def fetch_sequence_chunk(db_path: str, target_names: List[str]) -> Dict[str, str]:
        """Fetch multiple sequences from the database in a chunk."""
        sequences = {}
        try:
            with SequenceFile(db_path, digital=True) as seqfile:
                for sequence in seqfile:
                    seq_name = sequence.name.decode()
                    if seq_name in target_names:
                        # Convert digital sequence to text format
                        sequences[seq_name] = sequence.textize().sequence
                        if len(sequences) == len(target_names):
                            break
        except Exception as e:
            logger.error(f"Error fetching sequence chunk: {e}")
        
        return sequences

    @staticmethod
    def fetch_sequences_parallel(
        target_names: List[str], 
        db_path: str, 
        max_workers: int = 4, 
        chunk_size: int = 1000
    ) -> Dict[str, str]:
        """Fetch sequences in parallel using multiple workers."""
        all_sequences = {}
        
        # Split targets into chunks
        chunks = [
            target_names[i: i + chunk_size]
            for i in range(0, len(target_names), chunk_size)
        ]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {
                executor.submit(SequenceService.fetch_sequence_chunk, db_path, chunk): chunk
                for chunk in chunks
            }

            for future in as_completed(future_to_chunk):
                try:
                    chunk_sequences = future.result()
                    all_sequences.update(chunk_sequences)
                except Exception as e:
                    logger.error(f"Error in sequence chunk: {e}")

        return all_sequences 