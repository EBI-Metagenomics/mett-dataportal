from pathlib import Path
import tempfile
import os

from faa_sources import FtpFaaSource, SftpFaaSource, FaaConsolidator
from deduplicate_faa import deduplicate_faa


def get_sources(use_sftp=False):
    ftp_url = "http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15"
    sources = [FtpFaaSource(ftp_url)]

    if use_sftp:
        sftp_source = SftpFaaSource(
            host="codon-login",
            port=22,
            username="vikasg",
            base_dirs=[
                "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/spire_uniformis_mags_mettannotator_results",
                "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/mgnify_uniformis_mags_mettannotator_results",
                "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/mgnify_vulgatus_mags_mettannotator_results",
                "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/spire_vulgatus_mags_mettannotator_results2",
            ],
        )
        sources.append(sftp_source)

    return sources


def fetch_all_sequences(use_sftp=False):
    print("🔄 Fetching all .faa files from configured sources...")
    sources = get_sources(use_sftp=use_sftp)
    consolidator = FaaConsolidator(sources=sources, max_workers=3)

    all_entries = []
    for source in sources:
        results = consolidator._process_source_parallel(source)
        all_entries.extend(results)

    print(f"✅ Total sequences fetched: {len(all_entries)}")
    return all_entries  # List of (strain_id, content)


def consolidate_filtered(
    all_entries, output_filename, strain_prefixes=None, only_type_strains=False
):
    TYPE_STRAINS = {"BU_ATCC8492", "PV_ATCC8482"}

    filtered = []
    for strain_id, content in all_entries:
        if strain_prefixes and not any(
            strain_id.startswith(pfx) for pfx in strain_prefixes
        ):
            continue
        if only_type_strains and strain_id not in TYPE_STRAINS:
            continue
        filtered.append((strain_id, content))

    print(f"✂ Filtered sequences for {output_filename}: {len(filtered)}")
    output_path = Path("output") / output_filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        for _, content in filtered:
            f.write(content + "\n")

    return str(output_path)


def generate_deduplicated_isolates(all_entries, isolates_output_dir="output/isolates-db"):
    """
    Generate deduplicated FASTA files for each isolate.
    
    Args:
        all_entries: List of (strain_id, content) tuples
        isolates_output_dir: Directory to save deduplicated isolate files
    """
    print(f"🔄 Generating deduplicated files per isolate in {isolates_output_dir}...")
    
    # Create output directory
    isolates_path = Path(isolates_output_dir)
    isolates_path.mkdir(parents=True, exist_ok=True)
    
    TYPE_STRAINS = {"BU_ATCC8492", "PV_ATCC8482"}
    processed_count = 0
    
    for strain_id, content in all_entries:
        if not content.strip():
            print(f"⚠️  Skipping empty content for {strain_id}")
            continue
            
        print(f"🔍 Processing isolate: {strain_id}")
        
        # Create temporary file for the raw content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.faa', delete=False) as temp_file:
            temp_file.write(content)
            temp_input = temp_file.name
        
        try:
            # Generate output filename
            output_filename = f"{strain_id}_deduplicated.faa"
            output_path = isolates_path / output_filename
            
            # Deduplicate using existing function
            deduplicate_faa(
                input_faa=temp_input,
                output_faa=str(output_path),
                type_strains=TYPE_STRAINS
            )
            
            processed_count += 1
            print(f"✅ Generated: {output_path}")
            
        except Exception as e:
            print(f"✗ Error processing {strain_id}: {e}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_input)
            except OSError:
                pass
    
    print(f"🎯 Generated {processed_count} deduplicated isolate files in {isolates_output_dir}")
    return processed_count
