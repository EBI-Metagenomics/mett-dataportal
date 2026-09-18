# PPI API CURL Examples

This document provides CURL commands to test various scenarios for the PPI API endpoints.

## Prerequisites

Make sure the Django server is running:
```bash
cd dataportal_api
source set-env-dev.sh
python manage.py runserver
```

## Basic API Information

**Base URL:** `http://localhost:8000/api`

## 1. Health Check

```bash
curl -X GET "http://localhost:8000/api/health/"
```

## 2. Available Score Types

```bash
curl -X GET "http://localhost:8000/api/ppi/scores/available"
```

## 3. Basic PPI Interactions

### Get all interactions (default parameters)
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions"
```

### Get interactions for specific species
```bash
# Phocaeicola vulgatus
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV"

# Bacteroides uniformis
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=BU"
```

### Get interactions for specific isolates
```bash
# BU_ATCC8492 isolate
curl -X GET "http://localhost:8000/api/ppi/interactions?isolate_name=BU_ATCC8492"

# PV_ATCC8482 isolate
curl -X GET "http://localhost:8000/api/ppi/interactions?isolate_name=PV_ATCC8482"
```

### Get interactions with pagination
```bash
# First page, 10 results
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&page=1&per_page=10"

# Second page, 5 results
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&page=2&per_page=5"
```

## 4. Score-Based Filtering

### Filter by DS Score
```bash
# DS score >= 0.8
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8"

# DS score >= 0.9 (high confidence)
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.9"
```

### Filter by String Score
```bash
# String score >= 0.7
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=string_score&score_threshold=0.7"

# String score >= 0.5
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=string_score&score_threshold=0.5"
```

### Filter by Melt Score
```bash
# Melt score >= 0.9
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=melt_score&score_threshold=0.9"
```

### Filter by Abundance Score (GP Score)
```bash
# Abundance score >= 0.95
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=abundance_score&score_threshold=0.95"
```

## 5. Evidence-Based Filtering

### Filter by XL-MS Evidence
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&has_xlms=true"
```

### Filter by STRING Evidence
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&has_string=true"
```

### Filter by Operon Evidence
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&has_operon=true"
```

### Filter by EcoCyc Evidence
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&has_ecocyc=true"
```

### Filter by Experimental Evidence
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&has_xlms=true"
```

## 6. Score-Based Filtering

### High Score Interactions
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8"
```

### Medium Score Interactions
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.5"
```

### Low Score Interactions
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.2"
```

## 7. Protein-Specific Filtering

### Get interactions for a specific protein
```bash
# Replace A6KXK8 with an actual protein ID from your data
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&protein_id=A6KXK8"
```

## 8. Complex Filtering Scenarios

### High confidence + STRING evidence
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8&has_string=true"
```

### XL-MS + STRING evidence
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&has_xlms=true&has_string=true"
```

### DS score + STRING evidence
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8&has_string=true"
```

### Isolate + Score + Evidence filtering
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?isolate_name=BU_ATCC8492&score_type=ds_score&score_threshold=0.8&has_string=true"
```

## 9. Network Analysis

### Get Network Properties
```bash
# DS score network properties
curl -X GET "http://localhost:8000/api/ppi/network-properties?score_type=ds_score&score_threshold=0.8&species_acronym=PV"

# String score network properties
curl -X GET "http://localhost:8000/api/ppi/network-properties?score_type=string_score&score_threshold=0.7&species_acronym=PV"

# Melt score network properties
curl -X GET "http://localhost:8000/api/ppi/network-properties?score_type=melt_score&score_threshold=0.9&species_acronym=PV"
```

### Get Network Data
```bash
# DS score network data
curl -X GET "http://localhost:8000/api/ppi/network/ds_score?score_threshold=0.8&species_acronym=PV"

# String score network data
curl -X GET "http://localhost:8000/api/ppi/network/string_score?score_threshold=0.7&species_acronym=PV"
```

## 10. Protein Neighborhood Analysis

### Get protein neighborhood
```bash
# Replace A6KXK8 with an actual protein ID
curl -X GET "http://localhost:8000/api/ppi/neighborhood/A6KXK8?n=5&species_acronym=PV"

# Get more neighbors
curl -X GET "http://localhost:8000/api/ppi/neighborhood/A6KXK8?n=10&species_acronym=PV"
```

## 11. Error Testing

### Invalid species
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=INVALID"
```

### Invalid score type
```bash
curl -X GET "http://localhost:8000/api/ppi/network-properties?score_type=invalid_score&score_threshold=0.8&species_acronym=PV"
```

### Invalid protein ID
```bash
curl -X GET "http://localhost:8000/api/ppi/neighborhood/INVALID_PROTEIN?n=5&species_acronym=PV"
```

### Negative score threshold
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=-1"
```

## 12. Performance Testing

### Large page size
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&per_page=1000"
```

### Very high threshold (few results)
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.99"
```

### Very low threshold (many results)
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.1"
```

## 13. Pretty Print JSON Responses

To get nicely formatted JSON responses, pipe to `jq`:

```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&per_page=5" | jq '.'
```

## 14. Save Responses to Files

```bash
# Save interactions to file
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&per_page=100" -o pv_interactions.json

# Save network properties to file
curl -X GET "http://localhost:8000/api/ppi/network-properties?score_type=ds_score&score_threshold=0.8&species_acronym=PV" -o network_properties.json
```

## 15. Testing with Different Species

### Bacteroides uniformis (BU)
```bash
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=BU&per_page=10"
curl -X GET "http://localhost:8000/api/ppi/network-properties?score_type=ds_score&score_threshold=0.8&species_acronym=BU"
```

## Notes

1. **Replace protein IDs**: The examples use `A6KXK8` as a sample protein ID. Replace this with actual protein IDs from your data.

2. **Adjust thresholds**: The score thresholds (0.8, 0.9, etc.) are examples. Adjust based on your data and requirements.

3. **Pagination**: For large datasets, use pagination to avoid timeouts.

4. **Error handling**: The API returns appropriate HTTP status codes and error messages.

5. **Rate limiting**: Be mindful of API rate limits when running many requests.

## Quick Test Script

To run all basic tests quickly:

```bash
#!/bin/bash
echo "Testing PPI API endpoints..."

# Basic tests
curl -s "http://localhost:8000/api/health/" | jq '.'
curl -s "http://localhost:8000/api/ppi/scores/available" | jq '.'
curl -s "http://localhost:8000/api/ppi/interactions?species_acronym=PV&per_page=5" | jq '.'
curl -s "http://localhost:8000/api/ppi/network-properties?score_type=ds_score&score_threshold=0.8&species_acronym=PV" | jq '.'

echo "Basic tests completed!"
```
