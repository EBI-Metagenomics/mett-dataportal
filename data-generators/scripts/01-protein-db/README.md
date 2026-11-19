# METT protein database

One deduplicated protein FASTA for PyHMMER. Species, type strain, and isolate are filters over that file, not separate databases.

Identical amino-acid sequences collapse to one record. The representative name is the type-strain locus tag. Every member locus tag is stored in the header so a hit can still open the gene viewer:

```
>BU_ATCC8492_00001 sp=BU;PV st=BU_ATCC8492;PV_ATCC8482 ty=1 n=2 product=hypothetical protein lt=BU_ATCC8492_00001;PV_ATCC8482_00456
```

## Outputs

`data/generated/protein-db/` (override with `--out` or `params.out`):

- `mett_proteins.faa` — the search database
- `members.sqlite` — one row per locus tag, indexed for species, type-strain, and isolate filters
- `mett_proteins.faa.ssi` — random-access index, written when `esl-sfetch` is on `PATH`

The search form species list comes from the strain index. `members.tsv` is written while merging and removed once `members.sqlite` exists. A missing `/pub/databases/mett` FASTA is downloaded into `data/cache/faa`. `python3 run.py cleanup` removes a `members.tsv`, an older `catalog.json`, or a `faa-cache` left by an older run, and refuses to run when a search file is missing.

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

`run-local.sh` is the same sequence Nextflow runs, on this machine. `sources.tsv` keeps the cluster paths. A missing `/pub/databases/mett` FASTA is downloaded from `https://ftp.ebi.ac.uk/pub/databases/mett` into `data/cache/faa` and staged from that copy. Nextflow does the same during `STAGE`, so the workflow no longer requires those files to exist before it starts.

The 20hm rows point at `/pub/databases/metagenomics/temp`, which is not on the public site. When that path is missing, planning and staging use `data/generated/mettannotator/gff3_files/{isolate}/functional_annotation/prokka/{isolate}.faa` if it is there. Otherwise pass `--hm-root`.

```bash
python3 run.py plan --batch hd --jobs sources.tsv
python3 run.py plan --batch all --hm-root /Users/vikasg/Documents/mett-portal/ws/mett-dataportal/data-generators/data/generated/mettannotator/gff3_files/ --jobs sources.tsv
./run-local.sh
```

`--batch all` includes 20hm. `./run-local.sh sources.tsv ./chunks ../../data/generated/protein-db` overrides the input list, the chunk directory, and the output directory.

The script stages one JSONL chunk per isolate, then:

```bash
python3 run.py merge --chunks ./chunks --out ../../data/generated/protein-db
python3 run.py index \
  --faa ../../data/generated/protein-db/mett_proteins.faa \
  --members ../../data/generated/protein-db/members.tsv
```

`index` builds `members.sqlite`, writes the SSI file when `esl-sfetch` is available, then removes `members.tsv`. Point the API at the FASTA with `PYHMMER_DB`. `members.sqlite` is read from that same directory.
