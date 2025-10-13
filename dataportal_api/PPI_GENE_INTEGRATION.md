# PPI Import with Gene Information Integration

This document describes the enhanced PPI import functionality that includes gene information extracted from GFF files.

## Overview

The PPI import system has been enhanced to automatically extract and include gene information for each protein in protein-protein interactions. This information is sourced from GFF files and includes:

- `isolate_name`
- `locus_tag`
- `uniprot_id`
- `name`
- `seqid`
- `source`
- `type`
- `start`
- `end`
- `score`
- `strand`
- `phase`
- `product`

## Components

### 1. Enhanced PPI Model (`dataportal/models/interactions.py`)

The `ProteinProteinDocument` model now includes gene information fields for both proteins:

```python
# Gene Information for protein_a
protein_a_locus_tag = Keyword()
protein_a_uniprot_id = Keyword()
protein_a_name = Keyword()
# ... and more fields

# Gene Information for protein_b
protein_b_locus_tag = Keyword()
protein_b_uniprot_id = Keyword()
protein_b_name = Keyword()
# ... and more fields
```

### 2. GFF Parser (`dataportal/ingest/ppi/gff_parser.py`)

A new `GFFParser` class that:
- Downloads and parses GFF files from FTP servers
- Extracts gene information with caching to avoid re-downloading
- Provides methods to get gene information for specific proteins

Key features:
- **Caching**: In-memory cache to avoid re-downloading the same GFF files
- **FTP Integration**: Downloads GFF files from remote FTP servers
- **Error Handling**: Robust error handling for network and parsing issues
- **Memory Management**: Clears cache when needed

### 3. Enhanced Parsing Module (`dataportal/ingest/ppi/parsing.py`)

The `iter_ppi_rows` function now accepts an optional `GFFParser` parameter:

```python
def iter_ppi_rows(folder: str, pattern: str = "*.csv", gff_parser: Optional[GFFParser] = None) -> Iterator[Dict]:
```

When a GFF parser is provided, it automatically extracts gene information for each protein in the PPI.

### 4. Updated PPI Flow (`dataportal/ingest/ppi/flows/ppi_csv.py`)

The `PPICSVFlow` class now includes:
- Optional `gff_parser` parameter
- Integration of gene information into the indexing process
- Support for both proteins in each interaction

## Usage

### Using the Management Command

```bash
# Basic import with gene information
python manage.py import_ppi_with_genes --csv-folder /path/to/csv/files

# Import without gene information (faster)
python manage.py import_ppi_with_genes --csv-folder /path/to/csv/files --no-gene-info

# Custom FTP settings
python manage.py import_ppi_with_genes \
    --csv-folder /path/to/csv/files \
    --ftp-server ftp.example.com \
    --ftp-directory /path/to/gff/files

# Advanced options with refresh control
python manage.py import_ppi_with_genes \
    --csv-folder /path/to/csv/files \
    --batch-size 10000 \
    --refresh-every-rows 50000 \
    --refresh-every-secs 300.0 \
    --log-every 5000

# Custom index and refresh policy
python manage.py import_ppi_with_genes \
    --csv-folder /path/to/csv/files \
    --index my_custom_ppi_index \
    --refresh wait_for \
    --no-optimize-indexing
```

#### Available Arguments

- `--csv-folder`: Path to folder containing PPI CSV files (required)
- `--pattern`: File pattern to match CSV files (default: *.csv)
- `--ftp-server`: FTP server for GFF files (default: ftp.ebi.ac.uk)
- `--ftp-directory`: FTP directory for GFF files
- `--batch-size`: Batch size for indexing (default: 5000)
- `--log-every`: Log progress every N records (default: 100000)
- `--no-gene-info`: Skip gene information extraction (faster but no gene data)
- `--species-mapping`: Path to species mapping file (optional)
- `--index`: Elasticsearch index name (optional, uses default if not specified)
- `--refresh`: Refresh policy: true, false, or wait_for (default: wait_for)
- `--refresh-every-rows`: Refresh index every N rows (optional)
- `--refresh-every-secs`: Refresh index every N seconds (optional)
- `--no-optimize-indexing`: Disable indexing optimization (slower but uses less memory)

### Using the Python API

```python
from dataportal.ingest.ppi.gff_parser import GFFParser
from dataportal.ingest.ppi.flows.ppi_csv import PPICSVFlow
from dataportal.ingest.es_repo import PPIIndexRepository

# Initialize components
gff_parser = GFFParser()
repo = PPIIndexRepository()
species_map = {"Bacteroides uniformis": "BU", "Phocaeicola vulgatus": "PV"}

# Create flow with gene information
flow = PPICSVFlow(
    repo=repo,
    species_map=species_map,
    gff_parser=gff_parser  # This enables gene information extraction
)

# Run import
total_indexed = flow.run(
    folder="/path/to/csv/files",
    pattern="*.csv",
    batch_size=1000
)
```

## Configuration

### Species Mapping

The system uses a species mapping to determine which GFF files to download. You can customize this mapping:

```python
species_map = {
    "Bacteroides uniformis": "BU_ATCC8492",
    "Phocaeicola vulgatus": "PV_ATCC8482",
    # Add more species as needed
}
```

### FTP Configuration

The FTP server and directory arguments are properly used in the management command:

**Default FTP settings:**
- Server: `ftp.ebi.ac.uk`
- Directory: `/pub/databases/mett/annotations/v1_2024-04-15/`

**Command line usage:**
```bash
# Use custom FTP server
python manage.py import_ppi_with_genes \
    --csv-folder /path/to/csv/files \
    --ftp-server ftp.example.com \
    --ftp-directory /path/to/gff/files

# Use default FTP settings (no need to specify)
python manage.py import_ppi_with_genes --csv-folder /path/to/csv/files
```

**Python API usage:**
```python
gff_parser = GFFParser(
    ftp_server="your-ftp-server.com",
    ftp_directory="/path/to/gff/files"
)
```

**FTP Path Structure:**
The system expects GFF files to be located at:
```
{ftp_directory}/{isolate}/functional_annotation/merged_gff/{isolate}_annotations.gff
```

For example:
- `ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/BU_ATCC8492/functional_annotation/merged_gff/BU_ATCC8492_annotations.gff`

## Performance Considerations

### Caching

The GFF parser uses in-memory caching to avoid re-downloading the same GFF files. This significantly improves performance when processing multiple PPI records from the same species.

### Memory Usage

- GFF files are cached in memory after first download
- Use `gff_parser.clear_cache()` to free memory when needed
- Consider batch processing for large datasets

### Network Usage

- GFF files are downloaded once per species and cached
- Subsequent requests for the same species use cached data
- Consider running during off-peak hours for large imports

## Error Handling

The system includes robust error handling for:

- **Network Issues**: FTP connection failures, timeouts
- **File Issues**: Missing GFF files, corrupted downloads
- **Parsing Issues**: Malformed GFF files, missing attributes
- **Memory Issues**: Large file handling, cache management

## Troubleshooting

### Common Issues

1. **FTP Connection Errors**
   - Check network connectivity
   - Verify FTP server and directory paths
   - Check firewall settings

2. **Missing Gene Information**
   - Verify species mapping is correct
   - Check if GFF files exist for the species
   - Ensure locus_tag format matches between PPI and GFF data

3. **Memory Issues**
   - Clear GFF parser cache periodically
   - Reduce batch size
   - Process species separately

### Debugging

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Potential improvements for the future:

1. **Local GFF Storage**: Store GFF files locally to avoid repeated downloads
2. **Parallel Processing**: Process multiple species simultaneously
3. **Incremental Updates**: Only process changed GFF files
4. **Alternative Sources**: Support for other gene annotation sources
5. **Validation**: Cross-validate gene information between sources

## Examples

See `example_ppi_import_with_genes.py` for a complete working example of how to use the enhanced PPI import functionality.
