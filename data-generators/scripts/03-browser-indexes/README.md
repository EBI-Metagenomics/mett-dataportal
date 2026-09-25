# JBrowse index generation

Python CLIs index one FASTA or one GFF. A small planner turns a mapping TSV plus two input directories into that file list. Nextflow runs the planner once, then one task per file.

Bash is a poor fit here. The 20hm batch uses different roots, `.fna` assemblies, and isolate names that do not match the FASTA filename (`EB_ATCCBAA-613` vs `EB_ATCCBAA613.fna`). That matching already lives in the strain import mapping. Python can test it without a cluster, and Nextflow only has to execute the per-file commands.

## Requirements

See [requirements.txt](requirements.txt). The runtime scripts import only the Python 3.10+ standard library. `pip install -r requirements.txt` installs `pytest` for `tests/test_jobs.py`.

These commands must be on `PATH`. The scripts exit with the missing names if they are not.

| Command | Version run here | Used for | Package |
|---|---|---|---|
| `bgzip` | 1.21 | FASTA `.gz` + `.gzi`, GFF `.gz` | htslib |
| `samtools` | 1.21 | FASTA `.fai` (`samtools faidx`) | samtools |
| `tabix` | 1.21 | GFF `.tbi` | htslib |
| `jbrowse` | 4.1.13 | `sort-gff` and `text-index` | `@jbrowse/cli@4.1.13` (node >= 18.3) |

Nextflow 25.10.4 was used for `browser_indexes.nf`. The workflow needs Nextflow >= 22.10.

## What gets written

Output root defaults to `data-generators/data/generated/browser-indexes`. Layout matches the gene viewer (`{release}/{species}/fasta/{assembly}` and `{release}/{species}/gff3/{isolate}`).

FASTA (what `BgzipFastaAdapter` loads):

* `{assembly}.fa.gz` or `{assembly}.fna.gz`
* `{assembly}.fa.gz.fai` / `{assembly}.fna.gz.fai` (`samtools faidx`)
* `{assembly}.fa.gz.gzi` / `{assembly}.fna.gz.gzi` (`bgzip -i`)

GFF:

* trimmed at `##FASTA`, then `jbrowse sort-gff`
* `{isolate}_annotations.gff.gz` and `.tbi`
* `trix/{isolate}_annotations.gff.gz.ix`
* `trix/{isolate}_annotations.gff.gz.ixx`
* `trix/{isolate}_annotations.gff.gz_meta.json`

## Inputs

Both batches use the same GFF directory template:

`{base}/{isolate}/functional_annotation/merged_gff`

| | HD | 20hm |
|---|---|---|
| `--fasta-dir` | `/pub/databases/mett/all_hd_isolates/deduplicated_assemblies` | `/pub/databases/metagenomics/temp/mett/20hm/v1/assemblies` |
| `--gff-base` | `/pub/databases/mett/annotations/v1_2024-04-15` | `/pub/databases/metagenomics/temp/mett/20hm/v1/annotations` |
| `--map-tsv` | `data/reference/gff-assembly-prefixes.tsv` | `data/reference/gff-assembly-prefixes-20hm.tsv` |

`--map-tsv` is the same `prefix` / `assembly` file as `import_strains`. Override the annotation layout with `--gff-dir-template` (`{base}` and `{isolate}`).

## Local run

From this directory, for the 20hm batch:

```bash
python3 run.py run \
  --map-tsv ../../data/reference/gff-assembly-prefixes-20hm.tsv \
  --fasta-dir /pub/databases/metagenomics/temp/mett/20hm/v1/assemblies \
  --gff-base /pub/databases/metagenomics/temp/mett/20hm/v1/annotations \
  --release v1
```

HD is the same command with the HD paths and `gff-assembly-prefixes.tsv`.

`process_fasta.sh` and `process_gff3.sh` forward arguments to `run.py run --only fasta` and `--only gff`.

One file, which is also what each Nextflow task runs:

```bash
python3 index_fasta.py --fasta /path/AR_VPI0990.fna --out /tmp/fasta
python3 index_gff.py --gff /path/AR_VPI0990_annotations.gff --out /tmp/gff
```

## Nextflow

Requires Nextflow `>= 22.10` (header-aware `splitCsv`). Profiles `hd` and `20hm` set the paths above.

```bash
cd data-generators/scripts/03-browser-indexes
nextflow run browser_indexes.nf -profile 20hm
nextflow run browser_indexes.nf -profile hd --isolates BU_ATCC8492
nextflow run browser_indexes.nf -profile 20hm --only fasta --out /path/to/indexes
```

`--skip-missing` drops mapped isolates whose file is not on disk. `--index-base-url` prefixes absolute URIs into the trix metadata; otherwise those URIs stay relative (`trix/...`).
