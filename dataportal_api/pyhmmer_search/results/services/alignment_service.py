import io
import logging
from typing import List, Dict, Any

from .sequence_service import SequenceService

logger = logging.getLogger(__name__)


class AlignmentService:
    """Service for alignment and MSA processing."""

    @staticmethod
    def generate_enhanced_aligned_fasta_content(
        results: List[Dict[str, Any]], db_path: str, query_input: str
    ) -> bytes:
        """Generate enhanced aligned FASTA content using PyHMMER's hmmalign for proper MSA."""
        logger.info("Trying PyHMMER MSA generation first...")
        try:
            return AlignmentService.generate_pyhmmer_msa_content(
                results, db_path, query_input
            )
        except Exception as e:
            logger.warning(f"PyHMMER MSA generation failed: {e}")
            logger.info("Falling back to simple MSA generation...")
            try:
                return AlignmentService.generate_simple_msa_content(
                    results, db_path, query_input
                )
            except Exception as e2:
                logger.warning(f"Simple MSA generation failed: {e2}")
                logger.info("Falling back to fallback aligned FASTA generation...")
                return AlignmentService.generate_fallback_aligned_fasta_content(
                    results, db_path, query_input
                )

    @staticmethod
    def generate_pyhmmer_msa_content(
        results: List[Dict[str, Any]], db_path: str, query_input: str
    ) -> bytes:
        """Generate MSA content using PyHMMER's hmmalign - directly from other project."""
        try:
            import re
            from pyhmmer.easel import (
                TextSequence,
                DigitalSequenceBlock,
                Alphabet,
            )
            from pyhmmer.plan7 import Background, Builder
            from pyhmmer.hmmer import hmmalign

            # Parse query input exactly like the other project
            match = re.match(r"^>(.*$)\n([\s\S]+)", query_input, re.MULTILINE)
            if match is None:
                raise ValueError(f"Input query is faulty: {query_input}")

            header, input_sequence = match.groups()

            # Set up alphabet and background exactly like the other project
            alphabet = Alphabet.amino()
            background = Background(alphabet)
            builder = Builder(alphabet)

            # Build HMM from query sequence exactly like the other project
            # Clean the query sequence of any invalid characters
            input_sequence = "".join(
                char for char in input_sequence if char in "ACDEFGHIKLMNPQRSTVWY*"
            )

            sequence = TextSequence(name=header.encode(), sequence=input_sequence)
            hmm, _, _ = builder.build(sequence.digitize(alphabet), background)

            # Get target names and create a mapping
            target_names = [
                hit.get("target", "") for hit in results if hit.get("target")
            ]

            # Fetch sequences using the existing service that was working
            from .sequence_service import SequenceService

            all_sequences = SequenceService.fetch_sequences_parallel(
                target_names, db_path
            )

            # Create digital sequence block exactly like the other project
            digital_sequences = []

            # Add query sequence first
            digital_sequences.append(
                TextSequence(name=b"query", sequence=input_sequence).digitize(
                    Alphabet.amino()
                )
            )

            for hit in results:
                target = hit.get("target", "")
                if target and target in all_sequences:
                    sequence_str = all_sequences[target]

                    # Use domain coordinates if available (like the other project)
                    domains = hit.get("domains", [])
                    if domains:
                        domain = domains[0]
                        env_from = domain.get("env_from", 1)
                        env_to = domain.get("env_to", len(sequence_str))
                        # Extract domain sequence exactly like the other project
                        domain_sequence = sequence_str[env_from - 1 : env_to]
                    else:
                        domain_sequence = sequence_str

                    # Create name exactly like the other project
                    if domains:
                        domain = domains[0]
                        seq_name = f"{target}/{domain.get('env_from', 1)}-{domain.get('env_to', len(sequence_str))}".encode()
                    else:
                        seq_name = target.encode()

                    # Clean the sequence of any invalid characters
                    domain_sequence = "".join(
                        char
                        for char in domain_sequence
                        if char in "ACDEFGHIKLMNPQRSTVWY*"
                    )

                    digital_sequences.append(
                        TextSequence(name=seq_name, sequence=domain_sequence).digitize(
                            Alphabet.amino()
                        )
                    )

            if not digital_sequences:
                raise ValueError("No valid sequences found for alignment")

            # Create sequence block exactly like the other project
            sequence_block = DigitalSequenceBlock(Alphabet.amino(), digital_sequences)

            # Perform alignment using hmmalign exactly like the other project
            msa = hmmalign(hmm, sequence_block)

            # Debug: Let's see what we get from hmmalign
            logger.info(f"MSA type: {type(msa)}")
            logger.info(f"Number of sequences: {len(msa.sequences)}")

            # Write MSA to bytes buffer with all aligned sequences
            output = io.BytesIO()

            # Write all aligned sequences from MSA (including query)
            for i, aligned_sequence in enumerate(msa.alignment):
                seq_name = msa.sequences[i].name.decode()

                # Format the name properly
                if seq_name == "query":
                    output.write(f">query {header}\n".encode())
                else:
                    # Extract target name from the sequence name
                    if "/" in seq_name:
                        target_name = seq_name.split("/")[0]
                    else:
                        target_name = seq_name
                    output.write(f">{target_name}\n".encode())

                # Write the aligned sequence with gaps
                for j in range(0, len(aligned_sequence), 60):
                    output.write(aligned_sequence[j : j + 60].encode() + b"\n")

            content_bytes = output.getvalue()
            import gzip

            return gzip.compress(content_bytes)

        except Exception as e:
            logger.error(f"PyHMMER MSA generation failed: {e}")
            raise

    @staticmethod
    def convert_stockholm_to_fasta(stockholm_content: str) -> str:
        """Convert Stockholm format to FASTA format."""
        fasta_lines = []
        in_alignment = False

        for line in stockholm_content.split("\n"):
            line = line.strip()

            if line.startswith("# STOCKHOLM"):
                in_alignment = True
                continue
            elif line.startswith("//"):
                break
            elif line.startswith("#"):
                continue
            elif not line:
                continue
            elif in_alignment and not line.startswith("#"):
                # Parse sequence line
                parts = line.split()
                if len(parts) >= 2:
                    seq_name = parts[0]
                    sequence = parts[1]
                    fasta_lines.append(f">{seq_name}")
                    fasta_lines.append(sequence)

        return "\n".join(fasta_lines) + "\n"

    @staticmethod
    def generate_simple_msa_content(
        results: List[Dict[str, Any]], db_path: str, query_input: str
    ) -> bytes:
        """Generate simple MSA content using alignment data."""
        output = io.StringIO()

        # Get query sequence (first line after header)
        query_lines = query_input.strip().split("\n")
        if len(query_lines) >= 2:
            query_seq = query_lines[1]
        else:
            query_seq = ""

        # Write query sequence
        if query_seq:
            # Extract just the sequence name from the header, not the full header
            query_name = (
                query_lines[0].lstrip(">").split()[0]
                if query_lines[0].startswith(">")
                else "query"
            )
            output.write(f">query {query_name}\n")
            for i in range(0, len(query_seq), 60):
                output.write(query_seq[i : i + 60] + "\n")

        # Process each hit
        for hit in results:
            target = hit.get("target", "")
            description = hit.get("description", "")

            if not target:
                continue

            domains = hit.get("domains", [])
            if domains:
                domain = domains[0]
                alignment = domain.get("alignment", {})
                alignment_display = domain.get("alignment_display", {})

                if alignment:
                    # Use detailed alignment data
                    target_seq = alignment.get("target_sequence", "")
                    if target_seq:
                        output.write(f">{target} {description}\n")
                        for i in range(0, len(target_seq), 60):
                            output.write(target_seq[i : i + 60] + "\n")
                elif alignment_display:
                    # Use simple alignment display data - this should show the aligned sequence with gaps
                    target_seq = alignment_display.get("aseq", "")
                    if target_seq:
                        output.write(f">{target} {description}\n")
                        for i in range(0, len(target_seq), 60):
                            output.write(target_seq[i : i + 60] + "\n")
                    else:
                        # Fallback to database sequence if no alignment data
                        sequence = SequenceService.fetch_sequence_from_database(
                            target, db_path
                        )
                        if sequence:
                            output.write(f">{target} {description}\n")
                            for i in range(0, len(sequence), 60):
                                output.write(sequence[i : i + 60] + "\n")

        content = output.getvalue()
        content_bytes = content.encode("utf-8")
        import gzip

        return gzip.compress(content_bytes)

    @staticmethod
    def generate_fallback_aligned_fasta_content(
        results: List[Dict[str, Any]], db_path: str, query_input: str
    ) -> bytes:
        """Generate fallback aligned FASTA content using simple alignment display data."""
        output = io.StringIO()

        # Get query sequence
        query_lines = query_input.strip().split("\n")
        if len(query_lines) >= 2:
            query_seq = query_lines[1]
        else:
            query_seq = ""

        # Write query sequence
        if query_seq:
            # Extract just the sequence name from the header, not the full header
            query_name = (
                query_lines[0].lstrip(">").split()[0]
                if query_lines[0].startswith(">")
                else "query"
            )
            output.write(f">query {query_name}\n")
            for i in range(0, len(query_seq), 60):
                output.write(query_seq[i : i + 60] + "\n")

        # Process each hit
        for hit in results:
            target = hit.get("target", "")
            description = hit.get("description", "")

            if not target:
                continue

            domains = hit.get("domains", [])
            if domains:
                domain = domains[0]
                alignment = domain.get("alignment", {})
                alignment_display = domain.get("alignment_display", {})

                if alignment:
                    # Use detailed alignment data
                    query_seq = alignment.get("hmm_sequence", "")
                    target_seq = alignment.get("target_sequence", "")
                    identity_seq = alignment.get("identity_sequence", "")

                    if query_seq and target_seq:
                        output.write(f">{target}_query {description}\n")
                        for i in range(0, len(query_seq), 60):
                            output.write(query_seq[i : i + 60] + "\n")

                        output.write(f">{target}_target {description}\n")
                        for i in range(0, len(target_seq), 60):
                            output.write(target_seq[i : i + 60] + "\n")

                        if identity_seq:
                            output.write(f">{target}_identity {description}\n")
                            for i in range(0, len(identity_seq), 60):
                                output.write(identity_seq[i : i + 60] + "\n")
                elif alignment_display:
                    # Use simple alignment display data
                    query_seq = alignment_display.get("model", "")
                    target_seq = alignment_display.get("aseq", "")
                    match_line = alignment_display.get("mline", "")

                    logger.debug(
                        f"Alignment display for {target}: model={query_seq[:20]}..., aseq={target_seq[:20]}..."
                    )

                    if query_seq:
                        output.write(f">{target}_query {description}\n")
                        for i in range(0, len(query_seq), 60):
                            output.write(query_seq[i : i + 60] + "\n")
                    else:
                        output.write(f">{target}_query {description}\n")
                        output.write("N/A\n")

                    if target_seq:
                        output.write(f">{target}_target {description}\n")
                        for i in range(0, len(target_seq), 60):
                            output.write(target_seq[i : i + 60] + "\n")
                    else:
                        output.write(f">{target}_target {description}\n")
                        output.write("N/A\n")

                    if match_line:
                        output.write(f">{target}_match {description}\n")
                        for i in range(0, len(match_line), 60):
                            output.write(match_line[i : i + 60] + "\n")
            else:
                # No domains - try to get full sequence from database
                sequence = SequenceService.fetch_sequence_from_database(target, db_path)
                if sequence:
                    output.write(f">{target}_full {description}\n")
                    output.write(sequence)
                else:
                    output.write(f">{target} {description} (no domain data)\n")
                    output.write("N/A\n")

        content = output.getvalue()
        content_bytes = content.encode("utf-8")
        import gzip

        return gzip.compress(content_bytes)
