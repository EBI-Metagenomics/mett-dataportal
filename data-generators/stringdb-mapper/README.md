

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
  -o bu_to_string_raw.tsv \
  -f 6 qseqid sseqid pident length qcovhsp scovhsp evalue bitscore \
  --max-target-seqs 1 \
  --evalue 1e-5
```
```bash
$ diamond blastp \
  -q ./mett-faa-files/pv_typestrains.faa \
  -d pv435590_string \
  -o pv_to_string_raw.tsv \
  -f 6 qseqid sseqid pident length qcovhsp scovhsp evalue bitscore \
  --max-target-seqs 1 \
  --evalue 1e-5
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
### Turn this into a clean mapping table

From here:
```
Load mett_to_string_raw.tsv into pandas / a small script.
Filter by thresholds:
pident >= 80
qcovhsp >= 80
scovhsp >= 80
Write out a final mapping file:
mett_protein_id, mett_uniprot, string_protein_id, taxid, pident, qcov, scov
Then insert into your DB, e.g. protein_external_id:
protein_external_id
- protein_id      (FK → your protein table)
- source          = 'STRING'
- identifier      = '820.CUP55842'
- metadata        = { "taxid": 820, "pident": 99.1, ... }
```

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
