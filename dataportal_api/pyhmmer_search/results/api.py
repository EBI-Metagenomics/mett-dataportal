import gzip
import io
import json
import logging
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Query
from ninja.errors import HttpError

from dataportal.utils.response_wrappers import wrap_success_response
from .schemas import (
    JobDetailsResponseSchema,
    ResultQuerySchema,
    DomainDetailsResponseSchema,
    AlignmentDetailsResponseSchema
)
from ..search.models import HmmerJob, Database

logger = logging.getLogger(__name__)

pyhmmer_router_result = Router(tags=["PyHMMER Results"])


@pyhmmer_router_result.get("/{uuid:id}/download")
def download_results(request, id: uuid.UUID, format: str):
    """Download search results in various formats (tab, fasta, aligned_fasta)"""
    try:
        logger.info(f"=== DOWNLOAD REQUEST ===")
        logger.info(f"Job ID: {id}")
        logger.info(f"Format: {format}")

        # Validate format
        if format not in ['tab', 'fasta', 'aligned_fasta']:
            raise HttpError(400, f"Invalid format: {format}. Supported formats: tab, fasta, aligned_fasta")

        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data:
            raise HttpError(404, "No results found for this job")

        db_path = settings.HMMER_DATABASES.get(job.database)
        if not db_path:
            raise HttpError(500, f"Database {job.database} not configured")

        if format == 'tab':
            content = generate_tsv_content(result_data)
            filename = f"pyhmmer_hits_{id}.tsv"
            content_type = "text/tab-separated-values"
        elif format == 'fasta':
            content = generate_enhanced_fasta_content(result_data, db_path, job.input)
            filename = f"pyhmmer_hits_{id}.fasta.gz"
            content_type = "application/gzip"
            logger.info(f"Generated FASTA content type: {type(content)}")
            logger.info(f"Generated FASTA content length: {len(content)}")
        elif format == 'aligned_fasta':
            content = generate_enhanced_aligned_fasta_content(result_data, db_path, job.input)
            filename = f"pyhmmer_hits_{id}.aligned.fasta.gz"
            content_type = "application/gzip"
            logger.info(f"Generated aligned FASTA content type: {type(content)}")
            logger.info(f"Generated aligned FASTA content length: {len(content)}")

        # Create response
        if format in ['fasta', 'aligned_fasta']:
            if isinstance(content, str):
                content = content.encode('utf-8')

            # Test decompression to verify the content is valid
            try:
                test_decompressed = gzip.decompress(content)
                logger.info(f"Decompression test passed: {len(test_decompressed)} bytes")
            except Exception as decompress_error:
                logger.error(f"Decompression test failed: {decompress_error}")
                # If decompression fails, return uncompressed content
                logger.warning("Returning uncompressed content due to compression failure")
                content = generate_enhanced_fasta_content(result_data, db_path,
                                                          job.input) if format == 'fasta' else generate_enhanced_aligned_fasta_content(
                    result_data, db_path, job.input)
                if isinstance(content, str):
                    content = content.encode('utf-8')
                content_type = "text/plain"
                filename = filename.replace('.gz', '')

            response = HttpResponse(content, content_type=content_type)
        else:
            response = HttpResponse(content, content_type=content_type)

        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Log response details
        logger.info(f"Download generated successfully: {filename}")
        logger.info(f"Response content type: {content_type}")
        logger.info(f"Response content length: {len(content)} bytes")

        return response

    except Exception as e:
        logger.error(f"Error in download_results: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


def generate_tsv_content(results):
    """Generate TSV content from search results"""
    import csv

    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')

    # Write header
    writer.writerow([
        'Target', 'Description', 'E-value', 'Score', 'Bias',
        'Query_Start', 'Query_End', 'Target_Start', 'Target_End',
        'Query_Length', 'Target_Length', 'Identity_Pct', 'Identity_Count',
        'Similarity_Pct', 'Similarity_Count'
    ])

    # Write data rows
    for hit in results:
        target = hit.get('target', '')
        description = hit.get('description', '')
        evalue = hit.get('evalue', '')
        score = hit.get('score', '')

        # Get domain information if available
        domains = hit.get('domains', [])
        if domains:
            domain = domains[0]  # Use first domain
            bias = domain.get('bias', '')
            env_from = domain.get('env_from', '')
            env_to = domain.get('env_to', '')

            # Get alignment information
            alignment = domain.get('alignment', {})
            if alignment:
                query_start = alignment.get('hmm_from', '')
                query_end = alignment.get('hmm_to', '')
                target_start = alignment.get('target_from', '')
                target_end = alignment.get('target_to', '')
                query_length = alignment.get('hmm_length', '')
                target_length = alignment.get('target_length', '')
            else:
                query_start = query_end = target_start = target_end = query_length = target_length = ''

            # Get identity/similarity from alignment_display
            alignment_display = domain.get('alignment_display', {})
            if alignment_display:
                identity = alignment_display.get('identity', [0, 0])
                similarity = alignment_display.get('similarity', [0, 0])
                identity_pct = f"{identity[0] * 100:.1f}" if len(identity) > 0 else "0.0"
                identity_count = str(identity[1]) if len(identity) > 1 else "0"
                similarity_pct = f"{similarity[0] * 100:.1f}" if len(similarity) > 0 else "0.0"
                similarity_count = str(similarity[1]) if len(similarity) > 1 else "0"
            else:
                identity_pct = identity_count = similarity_pct = similarity_count = "0"
        else:
            bias = env_from = env_to = query_start = query_end = target_start = target_end = query_length = target_length = "0"
            identity_pct = identity_count = similarity_pct = similarity_count = "0"

        writer.writerow([
            target, description, evalue, score, bias,
            query_start, query_end, target_start, target_end,
            query_length, target_length, identity_pct, identity_count,
            similarity_pct, similarity_count
        ])

    return output.getvalue()


def fetch_sequence_from_database(target_name: str, db_path: str) -> str:
    """Fetch a sequence from the database file using PyHMMER"""
    try:
        from pyhmmer.easel import SequenceFile, SSIReader

        # Check if SSI index exists
        ssi_path = f"{db_path}.ssi"
        if os.path.exists(ssi_path):
            # Use SSI for fast lookup
            with SSIReader(ssi_path) as ssi_reader:
                try:
                    entry = ssi_reader.find_name(target_name.encode())
                    with open(db_path, 'rt') as fh:
                        fh.seek(entry.data_offset)
                        raw_sequence = fh.read(entry.record_length)

                        # Ensure proper FASTA format
                        if raw_sequence and not raw_sequence.startswith('>'):
                            return f">{target_name}\n{raw_sequence.strip()}\n"
                        elif raw_sequence:
                            if not raw_sequence.endswith('\n'):
                                raw_sequence += '\n'
                            return raw_sequence
                        else:
                            return ""

                except (KeyError, ValueError):
                    logger.warning(f"Target {target_name} not found in SSI index")

        # Fallback: scan through the file
        with SequenceFile(db_path, format="fasta") as seqfile:
            for seq in seqfile:
                if seq.name.decode() == target_name:
                    return f">{seq.name.decode()}\n{seq.sequence}\n"

        logger.warning(f"Target {target_name} not found in database")
        return ""

    except Exception as e:
        logger.error(f"Error fetching sequence for {target_name}: {e}")
        return ""


def fetch_sequence_chunk(db_path: str, target_names: List[str]) -> dict:
    """Fetch multiple sequences from database using SSI index in a single chunk"""
    try:
        from pyhmmer.easel import SSIReader

        sequences = {}
        ssi_path = f"{db_path}.ssi"

        if not os.path.exists(ssi_path):
            logger.warning(f"SSI index not found at {ssi_path}, falling back to individual fetching")
            return {name: fetch_sequence_from_database(name, db_path) for name in target_names}

        with SSIReader(ssi_path) as ssi_reader, open(db_path, "rt") as fh:
            for target_name in target_names:
                try:
                    entry = ssi_reader.find_name(target_name.encode())
                    fh.seek(entry.data_offset)
                    raw_sequence = fh.read(entry.record_length)

                    if raw_sequence and not raw_sequence.startswith('>'):
                        sequences[target_name] = f">{target_name}\n{raw_sequence.strip()}\n"
                    elif raw_sequence:
                        if not raw_sequence.endswith('\n'):
                            raw_sequence += '\n'
                        sequences[target_name] = raw_sequence
                    else:
                        sequences[target_name] = ""

                except (KeyError, ValueError) as e:
                    logger.warning(f"Target {target_name} not found in SSI index: {e}")
                    sequences[target_name] = ""

        return sequences

    except Exception as e:
        logger.error(f"Error fetching sequence chunk: {e}")
        return {name: "" for name in target_names}


def fetch_sequences_parallel(target_names: List[str], db_path: str, max_workers: int = 4,
                             chunk_size: int = 1000) -> dict:
    """Fetch multiple sequences in parallel using chunked approach"""
    if not target_names:
        return {}

    # Split targets into chunks
    chunks = [target_names[i:i + chunk_size] for i in range(0, len(target_names), chunk_size)]
    logger.info(f"Fetching {len(target_names)} sequences in {len(chunks)} chunks from database: {db_path}")

    all_sequences = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {
            executor.submit(fetch_sequence_chunk, db_path, chunk): chunk
            for chunk in chunks
        }

        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                chunk_sequences = future.result()
                all_sequences.update(chunk_sequences)
                logger.debug(f"Fetched {len(chunk_sequences)} sequences from chunk")
            except Exception as e:
                logger.error(f"Error fetching chunk {chunk}: {e}")
                # Add empty sequences for failed chunk
                for name in chunk:
                    all_sequences[name] = ""

    return all_sequences


def generate_enhanced_fasta_content(results, db_path: str, query_input: str):
    """Generate enhanced FASTA content with actual sequences from database"""
    output = io.StringIO()

    # Extract target names
    target_names = [hit.get('target', '') for hit in results if hit.get('target')]
    logger.info(f"Generating FASTA for {len(target_names)} targets")

    # Fetch sequences from database using improved chunking strategy
    sequences = fetch_sequences_parallel(target_names, db_path)
    logger.info(f"Fetched {len(sequences)} sequences from database")

    for hit in results:
        target = hit.get('target', '')
        description = hit.get('description', '')

        if target in sequences and sequences[target]:
            output.write(sequences[target])
            logger.debug(f"Used database sequence for {target}")
        else:
            sequence = None

            # Try to get from hit sequence field
            if hit.get('sequence'):
                sequence = hit.get('sequence')
            else:
                # Try to get from domain alignment data
                domains = hit.get('domains', [])
                if domains:
                    domain = domains[0]
                    alignment = domain.get('alignment', {})
                    if alignment and alignment.get('target_sequence'):
                        sequence = alignment.get('target_sequence').replace('-', '')
                    else:
                        alignment_display = domain.get('alignment_display', {})
                        if alignment_display and alignment_display.get('aseq'):
                            sequence = alignment_display.get('aseq').replace('-', '')

            # Write FASTA entry
            output.write(f">{target} {description}\n")
            if sequence:
                for i in range(0, len(sequence), 60):
                    output.write(sequence[i:i + 60] + "\n")
                logger.debug(f"Used fallback sequence for {target}")
            else:
                output.write("N/A\n")
                logger.warning(f"No sequence found for {target}")

    # Get the content and log its size
    content = output.getvalue()
    logger.info(f"Generated FASTA content size: {len(content)} characters")
    logger.debug(f"FASTA content preview: {content[:500]}...")

    # Validate FASTA format
    if not validate_fasta_content(content):
        logger.error("Generated FASTA content is not properly formatted!")
        # Try to fix common issues
        content = fix_fasta_content(content)
        if not validate_fasta_content(content):
            logger.error("Failed to fix FASTA content format")

    # Compress the content using modern gzip approach
    try:
        # Log the content before compression
        logger.info(f"Content to compress: {len(content)} characters")
        logger.debug(f"Content preview: {content[:200]}...")

        # Encode to bytes
        content_bytes = content.encode('utf-8')
        logger.info(f"Encoded content size: {len(content_bytes)} bytes")

        # Compress
        compressed_content = gzip.compress(content_bytes)
        logger.info(f"Compressed FASTA size: {len(compressed_content)} bytes")

        # Test decompression to verify it works
        try:
            decompressed = gzip.decompress(compressed_content).decode('utf-8')
            if decompressed == content:
                logger.info("Compression/decompression test passed")
            else:
                logger.warning("Compression/decompression test failed - content mismatch")
        except Exception as test_e:
            logger.error(f"Compression test failed: {test_e}")

        return compressed_content
    except Exception as e:
        logger.error(f"Error compressing FASTA content: {e}")
        # Fallback: return uncompressed content
        logger.warning("Returning uncompressed content due to compression error")
        return content.encode('utf-8')


def validate_fasta_content(content: str) -> bool:
    """Validate that the content is properly formatted FASTA"""
    lines = content.strip().split('\n')
    if not lines:
        return False

    # Check if it starts with a header
    if not lines[0].startswith('>'):
        logger.error("FASTA content doesn't start with '>'")
        return False

    # Check for alternating headers and sequences
    for i, line in enumerate(lines):
        if i % 2 == 0:  # Even lines should be headers
            if not line.startswith('>'):
                logger.error(f"Line {i + 1} should be a header but isn't: {line[:50]}")
                return False
        else:  # Odd lines should be sequences
            if line.startswith('>'):
                logger.error(f"Line {i + 1} should be a sequence but is a header: {line[:50]}")
                return False
            # Check if sequence contains only valid characters (DNA/RNA or protein)
            if line:
                valid_chars = set('ACGTNacgtnACDEFGHIKLMNPQRSTVWYXacdefghiklmnpqrstvwyx-*')
                invalid_chars = [c for c in line if c not in valid_chars]
                if invalid_chars:
                    logger.warning(
                        f"Line {i + 1} contains non-standard sequence characters: {line[:50]} (invalid chars: {invalid_chars[:10]})")

    return True


def fix_fasta_content(content: str) -> str:
    """Try to fix common FASTA formatting issues"""
    lines = content.strip().split('\n')
    fixed_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('>'):
            if not line.endswith('\n'):
                line += '\n'
            fixed_lines.append(line)
        else:
            valid_chars = set('ACGTNacgtnACDEFGHIKLMNPQRSTVWYXacdefghiklmnpqrstvwyx-*')
            sequence = ''.join(c for c in line if c in valid_chars)
            if sequence:
                fixed_lines.append(sequence)

    result = []
    for i in range(0, len(fixed_lines), 2):
        if i + 1 < len(fixed_lines):
            result.append(fixed_lines[i])
            result.append(fixed_lines[i + 1])
        else:
            result.append(fixed_lines[i])

    return '\n'.join(result) + '\n'


def generate_enhanced_aligned_fasta_content(results, db_path: str, query_input: str):
    """Generate enhanced aligned FASTA content using PyHMMER's hmmalign for proper MSA"""
    # First try the PyHMMER MSA approach
    logger.info("Trying PyHMMER MSA generation first...")
    try:
        return generate_pyhmmer_msa_content(results, db_path, query_input)
    except Exception as pyhmmer_error:
        logger.warning(f"PyHMMER MSA failed: {pyhmmer_error}")

    # If PyHMMER MSA fails, try the simple MSA approach
    logger.info("Trying simple MSA generation...")
    try:
        return generate_simple_msa_content(results, db_path, query_input)
    except Exception as simple_error:
        logger.warning(f"Simple MSA failed: {simple_error}")

    # If both fail, use fallback
    try:
        from pyhmmer.easel import Alphabet, Builder, TextSequence
        from pyhmmer.hmmer import hmmalign

        logger.info("Starting hmmalign-based alignment generation")

        # Parse query sequence
        query_match = re.match(r"^>(.*$)\n([\s\S]+)", query_input, re.MULTILINE)
        if query_match:
            query_header, query_sequence = query_match.groups()
            query_sequence = query_sequence.replace('\n', '').replace('\r', '')
            logger.info(f"Parsed query: {query_header} (length: {len(query_sequence)})")
        else:
            logger.warning("Could not parse query sequence, using fallback method")
            return generate_fallback_aligned_fasta_content(results, db_path, query_input)

        # Extract target names and domain information
        target_names = [hit.get('target', '') for hit in results if hit.get('target')]
        logger.info(f"Found {len(target_names)} targets")

        # Fetch sequences from database using improved chunking strategy
        sequences = fetch_sequences_parallel(target_names, db_path)
        logger.info(f"Fetched {len(sequences)} sequences from database")

        # Prepare sequences for alignment using domain information from PyHMMER results
        alignment_sequences = []

        for hit in results:
            target = hit.get('target', '')
            description = hit.get('description', '')
            domains = hit.get('domains', [])

            if target in sequences and sequences[target] and domains:
                # Parse the sequence from database
                seq_match = re.match(r"^>.*\n([\s\S]+)", sequences[target], re.MULTILINE)
                if seq_match:
                    full_sequence = seq_match.group(1).replace('\n', '').replace('\r', '')

                    # Get domain boundaries from PyHMMER results
                    domain = domains[0]  # Use first domain
                    env_from = domain.get('env_from', 1)
                    env_to = domain.get('env_to', len(full_sequence))

                    logger.debug(f"Domain for {target}: {env_from}-{env_to}")

                    # Extract domain sequence
                    domain_sequence = full_sequence[env_from - 1:env_to]

                    if domain_sequence:
                        alignment_sequences.append({
                            'name': f"{target}/{env_from}-{env_to}",
                            'description': description,
                            'sequence': domain_sequence
                        })
                        logger.debug(f"Added sequence {target}/{env_from}-{env_to} (length: {len(domain_sequence)})")

        logger.info(f"Prepared {len(alignment_sequences)} sequences for alignment")

        if not alignment_sequences:
            logger.warning("No valid sequences found for alignment, using fallback method")
            return generate_fallback_aligned_fasta_content(results, db_path, query_input)

        # Create HMM from query sequence
        alphabet = Alphabet.amino()
        builder = Builder(alphabet)

        query_seq = TextSequence(name=query_header.encode(), sequence=query_sequence)
        hmm, _, _ = builder.build(query_seq.digitize(alphabet))
        logger.info("Created HMM from query sequence")

        # Create digital sequences for alignment
        from pyhmmer.easel import DigitalSequenceBlock
        digital_sequences = []

        for seq_info in alignment_sequences:
            try:
                text_seq = TextSequence(
                    name=seq_info['name'].encode(),
                    sequence=seq_info['sequence']
                )
                digital_seq = text_seq.digitize(alphabet)
                digital_sequences.append(digital_seq)
                logger.debug(f"Created digital sequence for {seq_info['name']}")
            except Exception as seq_error:
                logger.error(f"Error creating digital sequence for {seq_info['name']}: {seq_error}")

        logger.info(f"Created {len(digital_sequences)} digital sequences")

        if not digital_sequences:
            logger.warning("No digital sequences created, using fallback method")
            return generate_fallback_aligned_fasta_content(results, db_path, query_input)

        # Perform multiple sequence alignment
        logger.info("Starting hmmalign...")
        msa = hmmalign(hmm, DigitalSequenceBlock(alphabet, digital_sequences))
        logger.info("hmmalign completed successfully")

        # Write MSA to string buffer
        output = io.StringIO()
        msa.write(output, "afa")
        content = output.getvalue()

        logger.info(f"Generated MSA with {len(alignment_sequences)} sequences")
        logger.debug(f"MSA content preview: {content[:500]}...")

        # Compress the content
        try:
            compressed_content = gzip.compress(content.encode('utf-8'))
            logger.info(f"Compressed aligned FASTA size: {len(compressed_content)} bytes")
            return compressed_content
        except Exception as e:
            logger.error(f"Error compressing aligned FASTA content: {e}")
            return content.encode('utf-8')

    except Exception as e:
        logger.error(f"Error in hmmalign-based alignment: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.warning("Falling back to simple alignment method")
        return generate_fallback_aligned_fasta_content(results, db_path, query_input)


def generate_pyhmmer_msa_content(results, db_path: str, query_input: str):
    """Generate MSA using PyHMMER's hmmalign API"""
    try:
        logger.info("Starting PyHMMER MSA generation")

        # Import PyHMMER modules
        from pyhmmer.easel import Alphabet, TextSequence
        from pyhmmer.plan7 import Builder, Background
        from pyhmmer.hmmer import hmmalign

        # Parse query sequence
        query_match = re.match(r"^>(.*$)\n([\s\S]+)", query_input, re.MULTILINE)
        if query_match:
            query_header, query_sequence = query_match.groups()
            query_sequence = query_sequence.replace('\n', '').replace('\r', '')
            logger.info(f"Parsed query: {query_header} (length: {len(query_sequence)})")
        else:
            raise ValueError("Could not parse query sequence")

        # Extract target names and domain information
        target_names = [hit.get('target', '') for hit in results if hit.get('target')]
        logger.info(f"Found {len(target_names)} targets")

        # Fetch sequences from database
        sequences = fetch_sequences_parallel(target_names, db_path)
        logger.info(f"Fetched {len(sequences)} sequences from database")

        # Prepare sequences for alignment
        alignment_sequences = []

        for hit in results:
            target = hit.get('target', '')
            description = hit.get('description', '')
            domains = hit.get('domains', [])

            if target in sequences and sequences[target] and domains:
                # Parse the sequence from database
                seq_match = re.match(r"^>.*\n([\s\S]+)", sequences[target], re.MULTILINE)
                if seq_match:
                    full_sequence = seq_match.group(1).replace('\n', '').replace('\r', '')

                    # Get domain boundaries
                    domain = domains[0]
                    env_from = domain.get('env_from', 1)
                    env_to = domain.get('env_to', len(full_sequence))

                    # Check if we have alignment coordinates (more precise)
                    alignment = domain.get('alignment', {})
                    if alignment:
                        target_from = alignment.get('target_from', env_from)
                        target_to = alignment.get('target_to', env_to)
                        logger.debug(f"Using alignment coordinates for {target}: {target_from}-{target_to}")
                        domain_sequence = full_sequence[target_from - 1:target_to]
                    else:
                        logger.debug(f"Using envelope coordinates for {target}: {env_from}-{env_to}")
                        domain_sequence = full_sequence[env_from - 1:env_to]

                    # Try to extract a larger region to see differences
                    # Add 50 amino acids on each side if possible
                    extended_from = max(1, (target_from if alignment else env_from) - 50)
                    extended_to = min(len(full_sequence), (target_to if alignment else env_to) + 50)
                    extended_sequence = full_sequence[extended_from - 1:extended_to]

                    logger.debug(
                        f"Extended region for {target}: {extended_from}-{extended_to} (length: {len(extended_sequence)})")
                    logger.debug(f"Extended sequence preview: {extended_sequence[:100]}...")

                    logger.debug(
                        f"Domain for {target}: {env_from}-{env_to}, full sequence length: {len(full_sequence)}")
                    logger.debug(f"Full sequence for {target}: {full_sequence[:100]}...")

                    logger.debug(
                        f"Extracted domain sequence for {target}: {domain_sequence[:50]}... (length: {len(domain_sequence)})")
                    logger.debug(
                        f"Domain boundaries check - env_from: {env_from}, env_to: {env_to}, extracted length: {len(domain_sequence)}")

                    if domain_sequence:
                        # Use extended sequence if the original domain is very short and all sequences might be identical
                        if len(domain_sequence) <= 50 and len(alignment_sequences) > 0:
                            # Check if this sequence is identical to the first one
                            if alignment_sequences[0]['sequence'] == domain_sequence:
                                logger.info(f"Sequence {target} is identical to first sequence, using extended region")
                                alignment_sequences.append({
                                    'name': f"{target}/{extended_from}-{extended_to} {description} (extended)",
                                    'description': description,
                                    'sequence': extended_sequence
                                })
                                logger.debug(
                                    f"Added extended sequence {target}/{extended_from}-{extended_to} (length: {len(extended_sequence)})")
                            else:
                                alignment_sequences.append({
                                    'name': f"{target}/{env_from}-{env_to} {description}",
                                    'description': description,
                                    'sequence': domain_sequence
                                })
                                logger.debug(
                                    f"Added sequence {target}/{env_from}-{env_to} (length: {len(domain_sequence)})")
                        else:
                            alignment_sequences.append({
                                'name': f"{target}/{env_from}-{env_to} {description}",
                                'description': description,
                                'sequence': domain_sequence
                            })
                            logger.debug(
                                f"Added sequence {target}/{env_from}-{env_to} (length: {len(domain_sequence)})")

        logger.info(f"Prepared {len(alignment_sequences)} sequences for alignment")

        # Debug: Print all domain boundaries
        logger.info("=== DOMAIN BOUNDARIES DEBUG ===")
        for seq_info in alignment_sequences:
            logger.info(f"Sequence: {seq_info['name']}, Length: {len(seq_info['sequence'])}")
            logger.info(f"First 50 chars: {seq_info['sequence'][:50]}")

        # Check if sequences are identical
        if len(alignment_sequences) > 1:
            first_seq = alignment_sequences[0]['sequence']
            all_identical = all(seq['sequence'] == first_seq for seq in alignment_sequences[1:])
            logger.info(f"All sequences identical: {all_identical}")
            if all_identical:
                logger.info(
                    "WARNING: All sequences are identical - this might indicate a problem with domain extraction")

        if not alignment_sequences:
            raise ValueError("No valid sequences found for alignment")

        # Create HMM from query sequence
        alphabet = Alphabet.amino()
        background = Background(alphabet)
        builder = Builder(alphabet)

        query_seq = TextSequence(name=query_header.encode(), sequence=query_sequence)
        hmm, _, _ = builder.build(query_seq.digitize(alphabet), background)
        logger.info("Created HMM from query sequence")

        # Create digital sequences for alignment
        from pyhmmer.easel import DigitalSequenceBlock
        digital_sequences = []

        for seq_info in alignment_sequences:
            text_seq = TextSequence(
                name=seq_info['name'].encode(),
                sequence=seq_info['sequence']
            )
            digital_seq = text_seq.digitize(alphabet)
            digital_sequences.append(digital_seq)

        logger.info(f"Created {len(digital_sequences)} digital sequences")

        # Perform multiple sequence alignment
        logger.info("Starting hmmalign...")
        msa = hmmalign(hmm, DigitalSequenceBlock(alphabet, digital_sequences))
        logger.info("hmmalign completed successfully")

        # Write MSA to binary buffer using AFA format (Aligned FASTA)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.afa', delete=False) as temp_file:
            msa.write(temp_file, "afa")
            temp_file.flush()

            # Read the content back as bytes and decode
            with open(temp_file.name, 'rb') as f:
                content_bytes = f.read()
                content = content_bytes.decode('utf-8')

            # Clean up
            import os
            os.unlink(temp_file.name)

        logger.info(f"Generated PyHMMER MSA with {len(alignment_sequences)} sequences")

        # Compress the content
        compressed_content = gzip.compress(content.encode('utf-8'))
        logger.info(f"Compressed PyHMMER MSA size: {len(compressed_content)} bytes")
        return compressed_content

    except Exception as e:
        logger.error(f"Error in PyHMMER MSA generation: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


def convert_stockholm_to_fasta(stockholm_content: str) -> str:
    """Convert Stockholm format MSA to FASTA format"""
    lines = stockholm_content.strip().split('\n')
    fasta_lines = []

    # Parse Stockholm format
    sequences = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        elif line.startswith('//'):
            break
        elif line.startswith('/'):
            continue
        elif ' ' in line:
            # Sequence line: name sequence
            parts = line.split(' ', 1)
            if len(parts) == 2:
                seq_name, sequence = parts
                if seq_name not in sequences:
                    sequences[seq_name] = ""
                sequences[seq_name] += sequence

    # Convert to FASTA format
    for seq_name, sequence in sequences.items():
        fasta_lines.append(f">{seq_name}")
        # Write sequence in 60-character lines
        for i in range(0, len(sequence), 60):
            fasta_lines.append(sequence[i:i + 60])

    return '\n'.join(fasta_lines) + '\n'


def generate_simple_msa_content(results, db_path: str, query_input: str):
    """Generate simple MSA using existing PyHMMER alignment data"""
    try:
        logger.info("Starting simple MSA generation using existing alignment data")

        # Parse query sequence
        query_match = re.match(r"^>(.*$)\n([\s\S]+)", query_input, re.MULTILINE)
        if query_match:
            query_header, query_sequence = query_match.groups()
            query_sequence = query_sequence.replace('\n', '').replace('\r', '')
        else:
            query_header = "query"
            query_sequence = ""

        output = io.StringIO()

        # Find sequences with alignment data
        aligned_sequences = []

        for hit in results:
            target = hit.get('target', '')
            description = hit.get('description', '')
            domains = hit.get('domains', [])

            if domains:
                domain = domains[0]
                alignment = domain.get('alignment', {})

                if alignment:
                    # Use PyHMMER alignment data
                    query_seq = alignment.get('hmm_sequence', '')
                    target_seq = alignment.get('target_sequence', '')

                    if query_seq and target_seq:
                        aligned_sequences.append({
                            'name': f"{target}",
                            'description': description,
                            'query_seq': query_seq,
                            'target_seq': target_seq
                        })

        if not aligned_sequences:
            logger.warning("No alignment data found, using fallback method")
            return generate_fallback_aligned_fasta_content(results, db_path, query_input)

        # Write aligned sequences in MSA format
        for seq_info in aligned_sequences:
            output.write(f">{seq_info['name']} {seq_info['description']}\n")
            # Write the aligned sequence with gaps
            aligned_seq = seq_info['target_seq']
            for i in range(0, len(aligned_seq), 60):
                output.write(aligned_seq[i:i + 60] + "\n")

        content = output.getvalue()
        logger.info(f"Generated simple MSA with {len(aligned_sequences)} sequences")

        # Compress the content
        try:
            compressed_content = gzip.compress(content.encode('utf-8'))
            logger.info(f"Compressed simple MSA size: {len(compressed_content)} bytes")
            return compressed_content
        except Exception as e:
            logger.error(f"Error compressing simple MSA content: {e}")
            return content.encode('utf-8')

    except Exception as e:
        logger.error(f"Error in simple MSA generation: {e}")
        return generate_fallback_aligned_fasta_content(results, db_path, query_input)


def generate_fallback_aligned_fasta_content(results, db_path: str, query_input: str):
    """Fallback method for aligned FASTA generation when hmmalign fails"""
    output = io.StringIO()

    # Parse query sequence
    query_match = re.match(r"^>(.*$)\n([\s\S]+)", query_input, re.MULTILINE)
    if query_match:
        query_header, query_sequence = query_match.groups()
        query_sequence = query_sequence.replace('\n', '').replace('\r', '')
    else:
        query_header = "query"
        query_sequence = ""

    # Extract target names
    target_names = [hit.get('target', '') for hit in results if hit.get('target')]

    # Fetch sequences from database using improved chunking strategy
    sequences = fetch_sequences_parallel(target_names, db_path)

    for hit in results:
        target = hit.get('target', '')
        description = hit.get('description', '')

        # Get alignment information
        domains = hit.get('domains', [])
        if domains:
            domain = domains[0]
            alignment = domain.get('alignment', {})
            alignment_display = domain.get('alignment_display', {})

            if alignment:
                # Use PyHMMER alignment data
                query_seq = alignment.get('hmm_sequence', '')
                target_seq = alignment.get('target_sequence', '')
                identity_seq = alignment.get('identity_sequence', '')

                output.write(f">{target}_query {description}\n")
                if query_seq:
                    for i in range(0, len(query_seq), 60):
                        output.write(query_seq[i:i + 60] + "\n")
                else:
                    output.write("N/A\n")

                output.write(f">{target}_target {description}\n")
                if target_seq:
                    for i in range(0, len(target_seq), 60):
                        output.write(target_seq[i:i + 60] + "\n")
                else:
                    output.write("N/A\n")

                if identity_seq:
                    output.write(f">{target}_identity {description}\n")
                    for i in range(0, len(identity_seq), 60):
                        output.write(identity_seq[i:i + 60] + "\n")
            elif alignment_display:
                # Use legacy alignment display data
                query_seq = alignment_display.get('model', '')
                target_seq = alignment_display.get('aseq', '')
                match_line = alignment_display.get('mline', '')

                output.write(f">{target}_query {description}\n")
                if query_seq:
                    for i in range(0, len(query_seq), 60):
                        output.write(query_seq[i:i + 60] + "\n")
                else:
                    output.write("N/A\n")

                output.write(f">{target}_target {description}\n")
                if target_seq:
                    for i in range(0, len(target_seq), 60):
                        output.write(target_seq[i:i + 60] + "\n")
                else:
                    output.write("N/A\n")

                if match_line:
                    output.write(f">{target}_match {description}\n")
                    for i in range(0, len(match_line), 60):
                        output.write(match_line[i:i + 60] + "\n")
            else:
                # No alignment data - try to get full sequence from database
                if target in sequences and sequences[target]:
                    output.write(f">{target}_full {description}\n")
                    output.write(sequences[target])
                else:
                    output.write(f">{target} {description} (no alignment data)\n")
                    output.write("N/A\n")
        else:
            # No domains - try to get full sequence from database
            if target in sequences and sequences[target]:
                output.write(f">{target}_full {description}\n")
                output.write(sequences[target])
            else:
                output.write(f">{target} {description} (no domain data)\n")
                output.write("N/A\n")

    # Compress the content using modern gzip approach
    content = output.getvalue()
    try:
        compressed_content = gzip.compress(content.encode('utf-8'))
        logger.info(f"Compressed fallback aligned FASTA size: {len(compressed_content)} bytes")
        return compressed_content
    except Exception as e:
        logger.error(f"Error compressing fallback aligned FASTA content: {e}")
        # Fallback: return uncompressed content
        logger.warning("Returning uncompressed fallback aligned FASTA content due to compression error")
        return content.encode('utf-8')


@pyhmmer_router_result.get("/{uuid:id}/debug-fasta")
def debug_fasta_generation(request, id: uuid.UUID):
    """Debug endpoint to test FASTA generation without compression"""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        # Parse the result
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data:
            raise HttpError(404, "No results found for this job")

        # Get database path
        db_path = settings.HMMER_DATABASES.get(job.database)
        if not db_path:
            raise HttpError(500, f"Database {job.database} not configured")

        # Generate uncompressed FASTA for debugging
        output = io.StringIO()
        target_names = [hit.get('target', '') for hit in result_data if hit.get('target')]
        sequences = fetch_sequences_parallel(target_names, db_path)

        for hit in result_data:
            target = hit.get('target', '')
            description = hit.get('description', '')

            if target in sequences and sequences[target]:
                output.write(sequences[target])
            else:
                output.write(f">{target} {description}\nN/A\n")

        content = output.getvalue()

        # Return uncompressed content for debugging
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = f'attachment; filename="debug_fasta_{id}.fasta"'
        return response

    except Exception as e:
        logger.error(f"Error in debug_fasta_generation: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/debug-aligned-fasta")
def debug_aligned_fasta_generation(request, id: uuid.UUID):
    """Debug endpoint to test aligned FASTA generation without compression"""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        # Parse the result
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data:
            raise HttpError(404, "No results found for this job")

        # Get database path
        db_path = settings.HMMER_DATABASES.get(job.database)
        if not db_path:
            raise HttpError(500, f"Database {job.database} not configured")

        # Generate uncompressed aligned FASTA for debugging
        output = io.StringIO()
        target_names = [hit.get('target', '') for hit in result_data if hit.get('target')]
        sequences = fetch_sequences_parallel(target_names, db_path)

        for hit in result_data:
            target = hit.get('target', '')
            description = hit.get('description', '')
            domains = hit.get('domains', [])

            if domains:
                domain = domains[0]
                alignment = domain.get('alignment', {})
                if alignment:
                    query_seq = alignment.get('hmm_sequence', '')
                    target_seq = alignment.get('target_sequence', '')

                    if query_seq:
                        output.write(f">{target}_query {description}\n{query_seq}\n")
                    if target_seq:
                        output.write(f">{target}_target {description}\n{target_seq}\n")
                else:
                    output.write(f">{target} {description} (no alignment data)\nN/A\n")
            else:
                output.write(f">{target} {description} (no domain data)\nN/A\n")

        content = output.getvalue()

        # Return uncompressed content for debugging
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = f'attachment; filename="debug_aligned_fasta_{id}.fasta"'
        return response

    except Exception as e:
        logger.error(f"Error in debug_aligned_fasta_generation: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/debug-pyhmmer-msa")
def debug_pyhmmer_msa_generation(request, id: uuid.UUID):
    """Debug endpoint to test PyHMMER MSA generation without compression"""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        # Parse the result
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data:
            raise HttpError(404, "No results found for this job")

        # Debug: Print raw HMMER results
        logger.info("=== RAW HMMER RESULTS DEBUG ===")
        for i, hit in enumerate(result_data[:3]):  # Show first 3 hits
            logger.info(f"Hit {i + 1}: {hit.get('target', 'N/A')}")
            domains = hit.get('domains', [])
            if domains:
                domain = domains[0]
                logger.info(f"  Domain env_from: {domain.get('env_from', 'N/A')}")
                logger.info(f"  Domain env_to: {domain.get('env_to', 'N/A')}")
                alignment = domain.get('alignment', {})
                if alignment:
                    logger.info(f"  Alignment target_from: {alignment.get('target_from', 'N/A')}")
                    logger.info(f"  Alignment target_to: {alignment.get('target_to', 'N/A')}")
            else:
                logger.info("  No domains found")

        # Get database path
        if hasattr(job.database, 'file') and job.database.file:
            db_path = job.database.file.path
        else:
            # Fallback to settings
            db_path = settings.HMMER_DATABASES.get(job.database)

        if not db_path:
            raise HttpError(500, "Database file not found")

        # Try to generate PyHMMER MSA content
        try:
            content = generate_pyhmmer_msa_content(result_data, db_path, job.input)
            if isinstance(content, bytes):
                # Check if it's compressed content
                if content.startswith(b'\x1f\x8b'):  # gzip magic number
                    content = gzip.decompress(content).decode('utf-8')
                else:
                    content = content.decode('utf-8')
        except Exception as msa_error:
            logger.error(f"PyHMMER MSA generation failed: {msa_error}")
            import traceback
            content = f"PyHMMER MSA generation failed: {msa_error}\n\nTraceback:\n{traceback.format_exc()}"

        # Return uncompressed content for debugging
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = f'attachment; filename="debug_pyhmmer_msa_{id}.fasta"'
        return response

    except Exception as e:
        logger.error(f"Error in debug_pyhmmer_msa_generation: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/debug-msa")
def debug_msa_generation(request, id: uuid.UUID):
    """Debug endpoint to test MSA generation without compression"""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        # Parse the result
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data:
            raise HttpError(404, "No results found for this job")

        # Get database path
        db_path = settings.HMMER_DATABASES.get(job.database)
        if not db_path:
            raise HttpError(500, f"Database {job.database} not configured")

        # Try to generate MSA content
        try:
            content = generate_enhanced_aligned_fasta_content(result_data, db_path, job.input)
            if isinstance(content, bytes):
                # Check if it's compressed content
                if content.startswith(b'\x1f\x8b'):  # gzip magic number
                    content = gzip.decompress(content).decode('utf-8')
                else:
                    content = content.decode('utf-8')
        except Exception as msa_error:
            logger.error(f"MSA generation failed: {msa_error}")
            content = f"MSA generation failed: {msa_error}\n\nFalling back to simple alignment..."

        # Return uncompressed content for debugging
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = f'attachment; filename="debug_msa_{id}.fasta"'
        return response

    except Exception as e:
        logger.error(f"Error in debug_msa_generation: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}", response=JobDetailsResponseSchema)
def get_result(request, id: uuid.UUID, query: Query[ResultQuerySchema]):
    from celery.result import AsyncResult

    try:
        logger.info(f"=== GET_RESULT CALLED ===")
        logger.info(f"Job ID: {id}")
        logger.info(f"Query params: {query}")

        logger.info(f"Fetching job from database...")
        job = get_object_or_404(HmmerJob, id=id)
        logger.info(f"Found job: {job}")
        logger.info(f"Job ID: {job.id}")
        logger.info(f"Job database: {job.database}")
        logger.info(f"Job threshold: {job.threshold}")
        logger.info(f"Job threshold_value: {job.threshold_value}")

        task_status = "PENDING"
        task_result_data = []

        if job.task:
            logger.info(f"Job has task: {job.task}")
            logger.info(f"Task ID: {job.task.task_id}")
            logger.info(f"Task status in DB: {job.task.status}")
            logger.info(f"Task date_created: {job.task.date_created}")
            logger.info(f"Task date_done: {job.task.date_done}")

            async_result = AsyncResult(job.task.task_id)
            task_status = async_result.status
            logger.info(f"AsyncResult status: {task_status}")
            logger.info(f"AsyncResult state: {async_result.state}")
            logger.info(f"AsyncResult info: {async_result.info}")
            logger.info(f"AsyncResult task_id: {async_result.task_id}")
            logger.info(f"Database task_id: {job.task.task_id}")
            logger.info(f"Task IDs match: {async_result.task_id == job.task.task_id}")

            # Get raw result from database
            raw_result = job.task.result
            logger.info(f"Raw result from database: {raw_result}")
            logger.info(f"Raw result type: {type(raw_result)}")
            logger.info(f"Raw result is None: {raw_result is None}")

            try:
                if raw_result is None:
                    logger.warning("Raw result is None, checking AsyncResult for fallback...")
                    if async_result.result is not None:
                        logger.info("Using AsyncResult result as fallback")
                        task_result_data = async_result.result
                    else:
                        logger.warning("Both database and AsyncResult have no result, setting empty list")
                        task_result_data = []
                elif isinstance(raw_result, str):
                    logger.info("Raw result is string, attempting JSON decode...")
                    import json
                    task_result_data = json.loads(raw_result)
                else:
                    logger.info("Raw result is already a list/dict, using as is")
                    task_result_data = raw_result
            except Exception as e:
                logger.error(f"Error parsing result: {e}")
                task_result_data = []

            logger.info(f"Parsed result data type: {type(task_result_data)}")
            logger.info(f"Result list length: {len(task_result_data) if isinstance(task_result_data, list) else 'N/A'}")
        else:
            logger.warning("Job has no task associated")

        logger.info(f"Final task_status: {task_status}")
        logger.info(f"Final task_result_data type: {type(task_result_data)}")
        logger.info(
            f"Final task_result_data length: {len(task_result_data) if isinstance(task_result_data, list) else 'N/A'}")

        if task_status != "SUCCESS":
            logger.info(f"Job not successful, returning status: {task_status}")
            response_data = {
                "status": task_status,
                "task": {
                    "status": job.task.status if job.task else "PENDING",
                    "date_created": job.task.date_created if job.task else None,
                    "date_done": job.task.date_done if job.task else None,
                    "result": None,
                },
                "database": None,
                "id": job.id,
                "algo": job.algo,
                "input": job.input,
                "threshold": job.threshold,
                "threshold_value": job.threshold_value,
            }
            logger.info(f"Returning non-success response: {response_data}")
            # Return the data directly for the wrapper to handle
            return response_data

        logger.info(f"Job is successful, getting database info...")
        db_config = settings.HMMER_DATABASES.get(job.database)
        if not db_config:
            logger.error(f"Database {job.database} not configured")
            raise HttpError(500, f"Database {job.database} not configured")

        try:
            database = Database.objects.get(id=job.database)
            logger.info(f"Found database: {database}")
        except Database.DoesNotExist:
            logger.error(f"Database with id {job.database} does not exist")
            raise HttpError(500, f"Database {job.database} not found")

        response_data = {
            "status": task_status,
            "task": {
                "status": job.task.status,
                "date_created": job.task.date_created,
                "date_done": job.task.date_done,
                "result": task_result_data or [],
            },
            "database": database,
            "id": job.id,
            "algo": job.algo,
            "input": job.input,
            "threshold": job.threshold,
            "threshold_value": job.threshold_value,
        }

        logger.info(f"=== RETURNING SUCCESS RESPONSE ===")
        logger.info(f"Response status: {response_data['status']}")
        logger.info(f"Response task status: {response_data['task']['status']}")
        logger.info(
            f"Response result length: {len(response_data['task']['result']) if response_data['task']['result'] else 0}")
        logger.info(f"Response preview: {response_data}")

        # Return the data directly for the wrapper to handle
        return response_data

    except Exception as e:
        logger.error(f"Error in get_result: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/domains", response=DomainDetailsResponseSchema)
def get_domains_by_target(request, id: uuid.UUID, target: str):
    """Get domains for a specific target in a search result."""
    try:
        logger.info(f"=== GET DOMAINS BY TARGET ===")
        logger.info(f"Job ID: {id}")
        logger.info(f"Target: {target}")

        job = get_object_or_404(HmmerJob, id=id)

        if not job.task:
            logger.error("Job has no task associated")
            raise HttpError(400, "Job not completed successfully")

        if job.task.status != "SUCCESS":
            logger.error(f"Job status is not SUCCESS: {job.task.status}")
            raise HttpError(400, f"Job not completed successfully, status: {job.task.status}")

        # Parse the result to get domain details
        result_data = None
        try:
            if isinstance(job.task.result, str):
                logger.info("Task result is string, attempting JSON decode...")
                import json
                result_data = json.loads(job.task.result)
                logger.info(f"Successfully parsed JSON result, type: {type(result_data)}")
            else:
                logger.info("Task result is not string, using as is")
                result_data = job.task.result or []
                logger.info(f"Using result as is, type: {type(result_data)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task result as JSON: {e}")
            logger.error(f"Task result type: {type(job.task.result)}")
            logger.error(f"Task result length: {len(job.task.result) if isinstance(job.task.result, str) else 'N/A'}")

            # Try to recover from truncated JSON
            if isinstance(job.task.result, str) and len(job.task.result) > 1000:
                logger.warning("Attempting to recover from potentially truncated JSON...")
                try:
                    # Try to find the last complete object
                    last_brace = job.task.result.rfind(']')
                    if last_brace > 0:
                        truncated_json = job.task.result[:last_brace + 1]
                        result_data = json.loads(truncated_json)
                        logger.warning(
                            f"Recovered from truncated JSON, got {len(result_data) if isinstance(result_data, list) else 0} results")
                    else:
                        raise ValueError("No valid JSON structure found")
                except Exception as recovery_error:
                    logger.error(f"Failed to recover from truncated JSON: {recovery_error}")
                    raise HttpError(500,
                                    f"Job result is corrupted and cannot be recovered. Please try the search again.")

            if result_data is None:
                raise HttpError(500, f"Failed to parse job result: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error parsing task result: {e}")
            raise HttpError(500, f"Error parsing job result: {str(e)}")

        if not result_data:
            logger.warning("No result data found")
            raise HttpError(404, "No results found for this job")

        if not isinstance(result_data, list):
            logger.error(f"Result data is not a list: {type(result_data)}")
            raise HttpError(500, "Invalid result format")

        # Find the target in the results
        target_data = None
        for item in result_data:
            if item.get('target') == target:
                target_data = item
                break

        if not target_data:
            logger.warning(f"Target '{target}' not found in results")
            logger.info(f"Available targets: {[item.get('target') for item in result_data[:5]]}")
            raise HttpError(404, f"Target '{target}' not found in results")

        domains = target_data.get('domains', [])
        logger.info(f"Found {len(domains)} domains for target {target}")

        # Return the data directly - the frontend will treat this as a legacy response
        return {
            "target": target_data.get('target', ''),
            "domains": domains
        }

    except HttpError:
        # Re-raise HttpError as is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_domains_by_target: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/domains/{int:domain_index}", response=DomainDetailsResponseSchema)
@wrap_success_response
def get_domain_details(request, id: uuid.UUID, domain_index: int):
    """Get detailed information about a specific domain in a search result."""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        # Parse the result to get domain details
        import json
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data or domain_index >= len(result_data):
            raise HttpError(404, "Domain not found")

        target_data = result_data[domain_index]
        domains = target_data.get('domains', [])

        return {
            "status": "success",
            "target": target_data.get('target', ''),
            "domains": domains
        }

    except Exception as e:
        logger.error(f"Error in get_domain_details: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/alignment/{int:domain_index}", response=AlignmentDetailsResponseSchema)
@wrap_success_response
def get_alignment_details(request, id: uuid.UUID, domain_index: int):
    """Get detailed alignment information for a specific domain."""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        # Parse the result to get alignment details
        import json
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data or domain_index >= len(result_data):
            raise HttpError(404, "Domain not found")

        target_data = result_data[domain_index]
        domains = target_data.get('domains', [])

        if not domains:
            raise HttpError(404, "No domains found for this target")

        # Return the first domain's alignment (you might want to add a domain parameter)
        domain = domains[0]

        return {
            "status": "success",
            "target": target_data.get('target', ''),
            "domain_index": domain_index,
            "alignment": domain.get('alignment'),
            "legacy_alignment": domain.get('alignment_display')
        }

    except Exception as e:
        logger.error(f"Error in get_alignment_details: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")
