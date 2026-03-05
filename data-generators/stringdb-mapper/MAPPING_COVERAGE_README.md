# Mapping Coverage Venn Diagram Analysis

## Overview

This workflow quantifies how many METT proteins successfully map to STRING identifiers for a given type strain, and produces data for Venn diagrams and verification.

**Sets for each strain:**
| Set | Description |
|-----|-------------|
| **METT proteins** | All proteins in the METT type-strain FASTA |
| **STRING proteins** | All proteins for the same taxon in STRING DB |
| **Successfully mapped** | METT proteins that mapped to a STRING protein via DIAMOND blastp |

## Quick Start

```bash
cd data-generators/stringdb-mapper

# Run for BU and PV
python mapping_coverage_venn.py --all

# Or for a single strain
python mapping_coverage_venn.py --strain BU
python mapping_coverage_venn.py --strain PV
```

## Output Files

All outputs go to `output/mapping_coverage/`:

| File | Description |
|------|-------------|
| `mapping_coverage_{BU,PV}.json` | Summary counts (JSON) |
| `mapping_coverage_{BU,PV}.tsv` | Summary table |
| `mapping_coverage_{BU,PV}_full.json` | Full data including all IDs |
| `unmapped_mett_{BU,PV}.txt` | METT protein IDs that failed to map |
| `unmatched_string_{BU,PV}.txt` | STRING protein IDs not hit by any METT |
| `venn_{bu,pv}.png` | Venn diagram (if matplotlib-venn installed) |

## Current Results

### BU (Bacteroides uniformis, taxon 820)
- METT proteins: 3,844
- STRING proteins: 3,899
- Successfully mapped: 3,444 (**89.6%** of METT)
- METT only (unmapped): 400
- STRING only (unmatched): 791

### PV (Bacteroides vulgatus, taxon 435590)
- METT proteins: 4,193
- STRING proteins: 4,065
- Successfully mapped: 3,943 (**94.0%** of METT)
- METT only (unmapped): 250
- STRING only (unmatched): 244

---

## Venn Diagram Tools

### Option 1: matplotlib-venn (Python, recommended)
```bash
pip install matplotlib matplotlib-venn
python mapping_coverage_venn.py --strain BU
# Produces output/mapping_coverage/venn_bu.png
```

### Option 2: InteractiVenn (web)
1. Go to [http://www.interactivenn.net/](http://www.interactivenn.net/)
2. Upload or paste your sets:
   - Set 1: METT proteins (use `mapping_coverage_BU_full.json` → `mett_only_ids` + `mapped_mett_ids`)
   - Set 2: STRING proteins (use `string_only_ids` + `string_ids_hit`)
3. Or use the counts: upload a CSV with `mett_only_unmapped`, `string_only_unmatched`, `successfully_mapped`

### Option 3: Venny (web)
- [https://bioinfogp.cnb.csic.es/tools/venny/](https://bioinfogp.cnb.csic.es/tools/venny/)
- Paste gene/protein lists or use list files

### Option 4: Python with only matplotlib (no matplotlib-venn)
Use the JSON counts to draw a custom diagram, or export counts for any tool.

---

## Cross-Verification Steps

### Step 1: Verify METT protein count
```bash
grep -c "^>" mett-faa-files/bu_typestrains.faa
# Expected: 3844 (BU) or 4193 (PV)
```

### Step 2: Verify STRING protein count
```bash
grep -c "^>" bu820_string.faa
# Expected: 3899 (BU) or 4065 for pv435590_string.faa (PV)
```

### Step 3: Verify mapping count
```bash
wc -l output/raw/bu_to_string_raw.tsv
# Expected: 3444 (BU) or 3943 (PV)
# Note: no header row in raw TSV
```

### Step 4: Verify set disjointness
```bash
# METT = mapped ∪ unmapped, and these are disjoint
cd output/mapping_coverage

# Count lines in unmapped
wc -l unmapped_mett_BU.txt
# Expected: 400

# Check: mapped + unmapped should equal total METT
echo $(( 3444 + 400 ))
# Expected: 3844 ✓
```

### Step 5: Spot-check unmapped METT proteins
Pick a few IDs from `unmapped_mett_BU.txt` and verify they do **not** appear in the raw TSV:
```bash
# Pick first unmapped ID
head -1 unmapped_mett_BU.txt
# e.g. BU_ATCC8492_00XXX

# Verify it's not in the mapping
grep "BU_ATCC8492_00XXX" output/raw/bu_to_string_raw.tsv
# Should return nothing
```

### Step 6: Spot-check mapped METT proteins
Pick a few IDs from the raw TSV and verify they **do** appear in the METT FASTA:
```bash
# Pick first mapped METT ID from raw output
cut -f1 output/raw/bu_to_string_raw.tsv | head -1
# e.g. BU_ATCC8492_00001

# Verify it's in METT FASTA
grep "BU_ATCC8492_00001" mett-faa-files/bu_typestrains.faa
# Should return the header line
```

### Step 7: Verify STRING IDs in mapping exist in STRING FASTA
```bash
# Get unique STRING IDs from mapping
cut -f2 output/raw/bu_to_string_raw.tsv | sort -u | wc -l
# This may be less than 3444 if multiple METT map to same STRING (many-to-one)

# Spot-check: first STRING ID from mapping
cut -f2 output/raw/bu_to_string_raw.tsv | head -1
# e.g. 820.ERS852554_01920

# Verify it exists in STRING FASTA
grep "820.ERS852554_01920" bu820_string.faa
# Should return the header line
```

### Step 8: Re-run and compare
```bash
python mapping_coverage_venn.py --strain BU
# Compare mapping_coverage_BU.json with previous run (e.g. in git)
# Counts should be stable if inputs haven't changed
```

---

## Adding a New Strain

Edit `mapping_coverage_venn.py` and add to `STRAIN_CONFIG`:

```python
"NEW_STRAIN": {
    "mett_faa": "mett-faa-files/new_typestrains.faa",
    "string_faa": "new_taxon_string.faa",
    "raw_tsv": "output/raw/new_to_string_raw.tsv",
    "taxon": 12345,
    "species": "Species name",
},
```

Then:
1. Ensure STRING FASTA is prepared (see main README)
2. Run DIAMOND blastp to produce `output/raw/new_to_string_raw.tsv`
3. Run: `python mapping_coverage_venn.py --strain NEW_STRAIN`
