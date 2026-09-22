# data-generators

Scripts that build portal artifacts, plus the local data those scripts and Django ingest consume.

Django ingest commands (species → strains → assays → networks) are documented in the [root README Data Import](../README.md#data-import) section.

## Layout

```
data-generators/
  scripts/
    01-faa-generator/       # protein FASTA pipeline for PyHMMER
    02-stringdb-mapper/     # METT → STRING mapping (Diamond + UniProt)
    03-browser-indexes/     # JBrowse FASTA/GFF indexes
    04-qc-duplicates/       # intra-strain duplicate QC
  data/
    reference/              # species.csv, gff-assembly-prefixes.tsv
    assays/Sub-Projects-Data/  # SP1–SP5 assay dumps (gitignored)
    inputs/stringdb/        # STRING proteomes, Diamond DBs, type-strain FASTA
    generated/              # script outputs
    legacy/                 # unused older CSVs
  docs/
    import-flow/            # genome import diagrams
    schema/                 # extended model (dbml/json)
```

Default paths are relative to this folder. Override with `FAA_OUT`, `STRING_INPUT_DIR`, `STRING_OUT`, `BROWSER_INDEX_OUT`, or `QC_OUT`.

Local PyHMMER env vars should point at `data/generated/faa/` and `data/generated/faa/isolates-db/` (not the old `faa-generator/output/` path).

## Script sequence

Numbering follows generator dependencies, not Django ingest order. Steps 03 and 04 are independent of 01–02.

| Step | Script | Consumes | Produces |
|---|---|---|---|
| 01 | `scripts/01-faa-generator/run_pipeline.py` | EBI FTP annotations | `data/generated/faa/` (type-strain, all-strain, per-isolate FASTAs) |
| 02 | `scripts/02-stringdb-mapper/` | `data/inputs/stringdb/` (STRING proteomes + type-strain FASTA from 01) | `data/generated/string-mapping/{raw,uniprot_mapped,mapping_coverage}` |
| 03 | `scripts/03-browser-indexes/` | EBI FTP FASTA + GFF | `data/generated/browser-indexes/` |
| 04 | `scripts/04-qc-duplicates/` | EBI FTP `.faa` | `data/generated/qc/` |
| 05 | `scripts/05-gff-add-gene-rows/` | CDS-only GFFs (20HM) | `data/generated/gff-with-genes/` (`gene` rows derived from CDS) |

```bash
# 01 — protein FASTAs (long-running)
cd scripts/01-faa-generator
python run_pipeline.py

# 02 — STRING mapping (needs Diamond DBs in data/inputs/stringdb)
cd ../02-stringdb-mapper
python convert_to_uniprot_mapping.py --help
python mapping_coverage_venn.py --all

# 03 — browser indexes
cd ../03-browser-indexes
./process_fasta.sh
./process_gff3.sh

# 04 — duplicate QC
cd ../04-qc-duplicates
python find_intra_strain_duplicates.py

# 05 — add gene rows to CDS-only GFFs (20HM)
cd ../05-gff-add-gene-rows
python add_gene_rows.py --input-dir /path/to/20hm-gffs
```

`process_gff3.sh` skips essentiality-track generation when `process_essentiality.sh` is absent (that helper is not in the repo).

Ingest then reads `data/reference/`, `data/Sub-Projects-Data/`, and `data/generated/string-mapping/`. See the root README for the `manage.py` command order.
