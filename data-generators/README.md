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
    05-mettannotator-prep/  # prune mettannotator results + add gene rows
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

Default paths are relative to this folder. Override with `FAA_OUT`, `STRING_INPUT_DIR`, `STRING_OUT`, `BROWSER_INDEX_OUT`, `QC_OUT`, or `METTANNOTATOR_OUT`.

Local PyHMMER env vars should point at `data/generated/faa/` and `data/generated/faa/isolates-db/` (not the old `faa-generator/output/` path).

## Script sequence

Numbering follows generator dependencies, not Django ingest order. Steps 03 and 04 are independent of 01–02.

| Step | Script | Consumes | Produces |
|---|---|---|---|
| 01 | `scripts/01-faa-generator/run_pipeline.py` | EBI FTP annotations | `data/generated/faa/` (type-strain, all-strain, per-isolate FASTAs) |
| 02 | `scripts/02-stringdb-mapper/` | `data/inputs/stringdb/` (STRING proteomes + type-strain FASTA from 01) | `data/generated/string-mapping/{raw,uniprot_mapped,mapping_coverage}` |
| 03 | `scripts/03-browser-indexes/` | Local or mounted FASTA + GFF (HD or 20hm roots) | `data/generated/browser-indexes/{release}/{species}/` |
| 04 | `scripts/04-qc-duplicates/` | EBI FTP `.faa` | `data/generated/qc/` |
| 05 | `scripts/05-mettannotator-prep/` | local `data/generated/mettannotator/` | pruned tree: `*_annotations.gff` with gene rows (`*-orig.gff` backup) + `prokka/{isolate}.faa` |

```bash
# 01 — protein FASTAs (long-running)
cd scripts/01-faa-generator
python run_pipeline.py

# 02 — STRING mapping (needs Diamond DBs in data/inputs/stringdb)
cd ../02-stringdb-mapper
python convert_to_uniprot_mapping.py --help
python mapping_coverage_venn.py --all

# 03 — browser indexes (paths required; see that folder's README)
cd ../03-browser-indexes
python3 run.py run \
  --map-tsv ../../data/reference/gff-assembly-prefixes.tsv \
  --fasta-dir /pub/databases/mett/all_hd_isolates/deduplicated_assemblies \
  --gff-base /pub/databases/mett/annotations/v1_2024-04-15

# 04 — duplicate QC
cd ../04-qc-duplicates
python find_intra_strain_duplicates.py

# 05 — prune mettannotator results and add gene rows (dry-run first)
cd ../05-mettannotator-prep
python prep_mettannotator.py
python prep_mettannotator.py --apply
```

Ingest then reads `data/reference/`, `data/Sub-Projects-Data/`, and `data/generated/string-mapping/`. See the root README for the `manage.py` command order.
