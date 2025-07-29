"""
FASTA service for PyHMMER FASTA generation and validation.
"""

import gzip
import io
import logging
from typing import List, Dict, Any

from .sequence_service import SequenceService

logger = logging.getLogger(__name__)


class FastaService:
    """Service for FASTA generation and validation."""

    @staticmethod
    def generate_enhanced_fasta_content(
        results: List[Dict[str, Any]], 
        db_path: str, 
        query_input: str
    ) -> bytes:
        """Generate enhanced FASTA content from search results."""
        output = io.StringIO()

        target_names = [hit.get("target", "") for hit in results if hit.get("target")]
        logger.info(f"Generating FASTA for {len(target_names)} targets")

        # Fetch sequences in parallel
        sequences = SequenceService.fetch_sequences_parallel(target_names, db_path)

        for hit in results:
            target = hit.get("target", "")
            description = hit.get("description", "")
            
            if not target:
                continue

            sequence = sequences.get(target, "")
            output.write(f">{target} {description}\n")

            if sequence:
                for i in range(0, len(sequence), 60):
                    output.write(sequence[i: i + 60] + "\n")
                logger.debug(f"Used fallback sequence for {target}")
            else:
                output.write("N/A\n")
                logger.warning(f"No sequence found for {target}")

        content = output.getvalue()
        logger.info(f"Generated FASTA content size: {len(content)} characters")
        logger.debug(f"FASTA content preview: {content[:500]}...")

        if not FastaService.validate_fasta_content(content):
            logger.error("Generated FASTA content is not properly formatted!")
            content = FastaService.fix_fasta_content(content)
            if not FastaService.validate_fasta_content(content):
                logger.error("Failed to fix FASTA content format")

        try:
            content_bytes = content.encode("utf-8")
            logger.info(f"Encoded content size: {len(content_bytes)} bytes")

            compressed_content = gzip.compress(content_bytes)
            logger.info(f"Compressed FASTA size: {len(compressed_content)} bytes")

            try:
                decompressed = gzip.decompress(compressed_content).decode("utf-8")
                logger.info(f"Decompression test passed: {len(decompressed)} characters")
            except Exception as decompress_error:
                logger.error(f"Decompression test failed: {decompress_error}")
                logger.warning("Returning uncompressed content due to compression error")
                return content_bytes

            return compressed_content

        except Exception as e:
            logger.error(f"Error compressing FASTA content: {e}")
            logger.warning("Returning uncompressed content due to compression error")
            return content.encode("utf-8")

    @staticmethod
    def validate_fasta_content(content: str) -> bool:
        """Validate FASTA content format."""
        if not content.strip():
            logger.error("FASTA content is empty")
            return False

        lines = content.strip().split("\n")
        if not lines:
            logger.error("FASTA content has no lines")
            return False

        if not lines[0].startswith(">"):
            logger.error("FASTA content doesn't start with '>'")
            return False

        for i, line in enumerate(lines):
            if i % 2 == 0:
                if not line.startswith(">"):
                    logger.error(f"Line {i + 1} should be a header but isn't: {line[:50]}")
                    return False
            else:
                if line.startswith(">"):
                    logger.error(
                        f"Line {i + 1} should be a sequence but is a header: {line[:50]}"
                    )
                    return False

        return True

    @staticmethod
    def fix_fasta_content(content: str) -> str:
        """Fix common FASTA content format issues."""
        lines = content.strip().split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            if i % 2 == 0:  # Header line
                if not line.startswith(">"):
                    fixed_lines.append(f">{line}")
                else:
                    fixed_lines.append(line)
            else:  # Sequence line
                # Remove any non-sequence characters
                cleaned_seq = "".join(c for c in line if c.isalpha() or c in "-*")
                if cleaned_seq:
                    fixed_lines.append(cleaned_seq)

        return "\n".join(fixed_lines) + "\n"

    @staticmethod
    def format_sequence_to_fasta(sequence: str, header: str) -> str:
        """Format a sequence into FASTA format."""
        fasta_lines = [header]
        
        # Write sequence in 60-character lines
        for i in range(0, len(sequence), 60):
            fasta_lines.append(sequence[i: i + 60])

        return "\n".join(fasta_lines) + "\n" 