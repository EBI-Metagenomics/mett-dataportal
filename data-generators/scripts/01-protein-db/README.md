# METT protein database

One deduplicated protein FASTA for PyHMMER. Species, type strain, and isolate are filters over that file, not separate databases.

Identical amino-acid sequences collapse to one record. The representative name is the type-strain locus tag. Every member locus tag is stored in the header so a hit can still open the gene viewer:

```
>BU_ATCC8492_00001 sp=BU;PV st=BU_ATCC8492;PV_ATCC8482 ty=1 n=2 product=hypothetical protein lt=BU_ATCC8492_00001;PV_ATCC8482_00456
```

## Outputs

`data/generated/protein-db/` (override with `--out` or `params.out`):

- `mett_proteins.faa` — the search database
- `members.tsv` — one row per locus tag
- `members.sqlite` — the same rows, indexed for search
- `catalog.json` — species list for the search form
- `mett_proteins.faa.ssi` — random-access index, written when `esl-sfetch` is on `PATH`

## Inputs

Isolates, not one directory per species. Each profile points at an annotation root and the isolate list that already exists.

| Profile | Root | Isolate list |
|---|---|---|
| `hd` | `/pub/databases/mett/annotations/v1_2024-04-15` | `data/reference/gff-assembly-prefixes.tsv` |
| `20hm` | `/pub/databases/metagenomics/temp/mett/20hm/v1/annotations` | `data/reference/gff-assembly-prefixes-20hm.tsv` |
| `all` | both | both |

FAA path template: `{root}/{isolate}/functional_annotation/prokka/{isolate}.faa`.

`type_strain_isolate` in `data/reference/species.csv` marks the type strain. A manifest can replace the profiles when a batch does not match the template. Columns: `isolate`, `species`, `faa`, `type_strain`, and optionally `collection`, `scientific_name`.

## Nextflow

Requires Nextflow `>= 22.10`.

```bash
nextflow run protein_db.nf -profile all
nextflow run protein_db.nf -profile hd
nextflow run protein_db.nf --manifest /path/sources.tsv
```

`MERGE` is the heavy step. One task collects every isolate chunk, deduplicates on the sequence, and writes the FASTA.

## Local run

Same steps Nextflow runs, without a cluster:

```bash
python3 run.py plan --batch hd --jobs sources.tsv
python3 run.py stage --faa /path/BU_ATCC8492.faa --isolate BU_ATCC8492 --species BU --type-strain --collection hd --out BU_ATCC8492.jsonl
python3 run.py merge --chunks ./chunks --out ../../data/generated/protein-db
python3 run.py index --faa ../../data/generated/protein-db/mett_proteins.faa --members ../../data/generated/protein-db/members.tsv
```

Point the API at the FASTA with `PYHMMER_DB`. `members.sqlite` and `catalog.json` are read from the same directory.
