### Mapping coverage Venn diagram

To quantify how many METT proteins map to STRING identifiers:

```bash
python mapping_coverage_venn.py --all
```

See [MAPPING_COVERAGE_README.md](MAPPING_COVERAGE_README.md) for output files, verification steps, and Venn diagram tools.

---

### Convert the STRING DB FASTA for DIAMOND:
```bash
$ zcat ./stringdb-protein-files/820.protein.sequences.v12.0.fa.gz \
  | awk '{print ">" $1 "\n" $2}' \
  > bu820_string.faa
```

```bash
$ zcat ./stringdb-protein-files/435590.protein.sequences.v12.0.fa.gz \
  | awk '{print ">" $1 "\n" $2}' \
  > pv435590_string.faa
```

#### sanity-check:
head -4 bu820_string.faa
Should look like:
>820.CUP55842
MSEIDHVGLWNRCLEIIRDNVPEQTYK...
>820.CUP55843
MKLT...


### Build a DIAMOND database from the STRING proteome

#### Install DIAMOND if you haven’t already (conda is easiest):
```bash
$ conda install -c bioconda diamond
```
OR
```bash
$ conda create -n diamond -c conda-forge -c bioconda python=3.11 diamond
```

#### Then build the DB:
```bash
$ diamond makedb \
  --in bu820_string.faa \
  -d bu820_string
```
```bash
$ diamond makedb \
  --in pv435590_string.faa \
  -d pv435590_string
```
This will create bu820_string.dmnd.

### Prepare METT BU type-strain proteins as FASTA

Example expected format:
``` 
>BU_METT_00001 A7V2E8 some description...
MSEIDHVGLWNRCLEIIRDNV...
>BU_METT_00002 Q9XXXX ...
```
Let’s call this file:
mett_bu_type_strain.faa


### Run DIAMOND blastp to map METT proteins → STRING proteins
Run a blastp-like search:
Basic best-hit mapping:
```bash
$ diamond blastp \
  -q ./mett-faa-files/bu_typestrains.faa \
  -d bu820_string \
  -o ./output/raw/bu_to_string_raw.tsv \
  -f 6 qseqid sseqid pident length qcovhsp scovhsp evalue bitscore \
  --max-target-seqs 1  \
  --evalue 1e-3 \
  --more-sensitive
```
```bash
$ diamond blastp \
  -q ./mett-faa-files/pv_typestrains.faa \
  -d pv435590_string \
  -o ./output/raw/pv_to_string_raw.tsv \
  -f 6 qseqid sseqid pident length qcovhsp scovhsp evalue bitscore \
  --max-target-seqs 1  \
  --evalue 1e-3 \
  --more-sensitive
```

**Explanation:**
```
-q – METT BU proteins
-d – STRING BU DB
-f 6 ... – custom tabular format with:
qseqid – METT protein ID
sseqid – STRING protein ID (e.g. 820.CUP55842)
pident – % identity
length – alignment length
qcovhsp – % query coverage of the HSP
scovhsp – % subject coverage of the HSP
evalue, bitscore – standard stats
--max-target-seqs 1 – only keep the single best hit per query.
```

### Add stricter filters if required:
```
  --id 70 \
  --query-cover 70 \
  --subject-cover 70
```
for at least 70% identity and 70% coverage. (You can tune those once you see the distribution.)


### Inspect and validate the mapping
Look at a few lines:
head mett_to_string_raw.tsv
You should see something like:
```
BU_METT_00001  820.CUP55842  99.1  461  100.0  100.0  1e-150  550
BU_METT_00002  820.CUP55843  97.3  380   95.0   96.0  3e-120  430
```

**Interpretation:**
```
BU_METT_00001 ↔ 820.CUP55842 with 99.1% identity, full-length.
That 820.CUP55842 is what you’ll later send to STRING’s PPI endpoints as identifiers=820.CUP55842&species=820.
If you want to separate the numeric taxid and the CUP ID, you can split sseqid later in Python or SQL (split_part).
```
### Convert to UniProt→STRING mapping (for PPI import)

PPI data uses UniProt IDs; the raw DIAMOND output uses locus_tags. Run the conversion script to produce UniProt-keyed mappings:

```bash
# BU (downloads GFF from FTP)
python convert_to_uniprot_mapping.py \
  --raw-tsv output/raw/bu_to_string_raw.tsv \
  --download-gff BU_ATCC8492 \
  --output output/uniprot_mapped/bu_uniprot_to_string.tsv

# PV
python convert_to_uniprot_mapping.py \
  --raw-tsv output/raw/pv_to_string_raw.tsv \
  --download-gff PV_ATCC8482 \
  --output output/uniprot_mapped/pv_uniprot_to_string.tsv
```

Or with a local GFF file:
```bash
python convert_to_uniprot_mapping.py \
  --raw-tsv output/raw/bu_to_string_raw.tsv \
  --gff-file /path/to/BU_ATCC8492/.../merged_annotations.gff \
  --output output/uniprot_mapped/bu_uniprot_to_string.tsv
```

Then point PPI import at the output directory:
```bash
python manage.py import_ppi_with_genes \
  --csv-folder /path/to/ppi_csvs \
  --string-mapping-dir output/uniprot_mapped/
```

The output TSV has columns: `locus_tag`, `uniprot_id`, `string_protein_id`.

Both locus_tag and uniprot_id can be used for lookups at different stages (e.g. PPI import uses uniprot_id; feature/other workflows may use locus_tag).

### Using it in PPI module
Call STRING:
```
https://string-db.org/api/tsv/network?identifiers=820.CUP55842&species=820&caller_identity=mett-portal
```
Parse edges, merge with your internal PPIs, classify intra/inter/cross as planned.

### Downloads from string DB
```html 
https://string-db.org/cgi/download?sessionId=bOOcopaODBCk&species_text=Bacteroides+vulgatus+ATCC+8482&settings_expanded=0&min_download_score=0&filter_redundant_pairs=0&delimiter_type=txt
```
