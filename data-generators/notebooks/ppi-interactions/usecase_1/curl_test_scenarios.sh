#!/bin/bash

# PPI API Test Scenarios using CURL
# Make sure the Django server is running: python manage.py runserver

API_BASE_URL="http://localhost:8000/api"

echo "=========================================="
echo "PPI API Test Scenarios"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to make API call and display results
test_endpoint() {
    local test_name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="$4"
    
    echo -e "\n${BLUE}Testing: $test_name${NC}"
    echo "URL: $url"
    echo "Method: $method"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$url")
    else
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    http_code=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS:/d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
        echo "Response preview:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body" | head -10
    else
        echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
        echo "Error response:"
        echo "$body"
    fi
    echo "----------------------------------------"
}

# 1. Basic Health Check
test_endpoint "Health Check" "$API_BASE_URL/health/"

# 2. Get Available Score Types
test_endpoint "Available Score Types" "$API_BASE_URL/ppi/scores/available"

# 3. Basic PPI Interactions - Default Parameters
test_endpoint "Basic PPI Interactions (Default)" "$API_BASE_URL/ppi/interactions"

# 4. PPI Interactions - Species Filter
test_endpoint "PPI Interactions - PV Species" "$API_BASE_URL/ppi/interactions?species_acronym=PV"
  
test_endpoint "PPI Interactions - BU Species" "$API_BASE_URL/ppi/interactions?species_acronym=BU"

# 5. PPI Interactions - Score Filtering
test_endpoint "PPI Interactions - DS Score >= 0.8" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8"

test_endpoint "PPI Interactions - String Score >= 0.7" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=string_score&score_threshold=0.7"

test_endpoint "PPI Interactions - Melt Score >= 0.9" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=melt_score&score_threshold=0.9"

# 6. PPI Interactions - Evidence Filtering
test_endpoint "PPI Interactions - With XL-MS Evidence" "$API_BASE_URL/ppi/interactions?species_acronym=PV&has_xlms=true"

test_endpoint "PPI Interactions - With STRING Evidence" "$API_BASE_URL/ppi/interactions?species_acronym=PV&has_string=true"

test_endpoint "PPI Interactions - With XL-MS Evidence" "$API_BASE_URL/ppi/interactions?species_acronym=PV&has_xlms=true"

# 7. PPI Interactions - Score Filtering
test_endpoint "PPI Interactions - High Score" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8"

test_endpoint "PPI Interactions - Medium Score" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.5"

# 8. PPI Interactions - Pagination
test_endpoint "PPI Interactions - Page 1 (5 per page)" "$API_BASE_URL/ppi/interactions?species_acronym=PV&page=1&per_page=5"

test_endpoint "PPI Interactions - Page 2 (5 per page)" "$API_BASE_URL/ppi/interactions?species_acronym=PV&page=2&per_page=5"

# 9. PPI Interactions - Protein Filter
test_endpoint "PPI Interactions - Specific Protein" "$API_BASE_URL/ppi/interactions?species_acronym=PV&protein_id=A6KXK8"

# 10. Network Properties - Different Score Types
test_endpoint "Network Properties - DS Score" "$API_BASE_URL/ppi/network-properties?score_type=ds_score&score_threshold=0.8&species_acronym=PV"

test_endpoint "Network Properties - String Score" "$API_BASE_URL/ppi/network-properties?score_type=string_score&score_threshold=0.7&species_acronym=PV"

test_endpoint "Network Properties - Melt Score" "$API_BASE_URL/ppi/network-properties?score_type=melt_score&score_threshold=0.9&species_acronym=PV"

# 11. Network Data - Different Score Types
test_endpoint "Network Data - DS Score" "$API_BASE_URL/ppi/network/ds_score?score_threshold=0.8&species_acronym=PV"

test_endpoint "Network Data - String Score" "$API_BASE_URL/ppi/network/string_score?score_threshold=0.7&species_acronym=PV"

# 12. Protein Neighborhood - Different Proteins
test_endpoint "Protein Neighborhood - A6KXK8" "$API_BASE_URL/ppi/neighborhood/A6KXK8?n=5&species_acronym=PV"

# Try to get a protein from the interactions first
echo -e "\n${YELLOW}Getting a sample protein for neighborhood test...${NC}"
sample_response=$(curl -s "$API_BASE_URL/ppi/interactions?species_acronym=PV&per_page=1")
sample_protein=$(echo "$sample_response" | jq -r '.data[0].protein_a' 2>/dev/null)

if [ "$sample_protein" != "null" ] && [ -n "$sample_protein" ]; then
    test_endpoint "Protein Neighborhood - Sample Protein" "$API_BASE_URL/ppi/neighborhood/$sample_protein?n=3&species_acronym=PV"
else
    echo -e "${YELLOW}Could not get sample protein for neighborhood test${NC}"
fi

# 13. Error Cases
echo -e "\n${YELLOW}Testing Error Cases...${NC}"

test_endpoint "Invalid Species" "$API_BASE_URL/ppi/interactions?species_acronym=INVALID"

test_endpoint "Invalid Score Type" "$API_BASE_URL/ppi/network-properties?score_type=invalid_score&score_threshold=0.8&species_acronym=PV"

test_endpoint "Invalid Protein ID" "$API_BASE_URL/ppi/neighborhood/INVALID_PROTEIN?n=5&species_acronym=PV"

test_endpoint "Negative Score Threshold" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=-1"

# 14. Complex Filtering Scenarios
test_endpoint "Complex Filter - High Score + String Evidence" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8&has_string=true"

test_endpoint "Complex Filter - XL-MS + STRING Evidence" "$API_BASE_URL/ppi/interactions?species_acronym=PV&has_xlms=true&has_string=true"

test_endpoint "Complex Filter - Multiple Score Types" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8&has_string=true"

# 15. Performance Tests
echo -e "\n${YELLOW}Performance Tests...${NC}"

test_endpoint "Large Page Size" "$API_BASE_URL/ppi/interactions?species_acronym=PV&per_page=1000"

test_endpoint "High Threshold (Few Results)" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.99"

test_endpoint "Low Threshold (Many Results)" "$API_BASE_URL/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.1"

echo -e "\n${GREEN}=========================================="
echo "All tests completed!"
echo "==========================================${NC}"

# Summary of all endpoints tested
echo -e "\n${BLUE}Summary of Tested Endpoints:${NC}"
echo "1. Health check"
echo "2. Available score types"
echo "3. Basic interactions (default parameters)"
echo "4. Species filtering (PV, BU)"
echo "5. Score filtering (ds_score, string_score, melt_score)"
echo "6. Evidence filtering (xlms, string, experimental)"
echo "7. Confidence filtering (high, medium)"
echo "8. Pagination (page, per_page)"
echo "9. Protein-specific filtering"
echo "10. Network properties (different score types)"
echo "11. Network data (different score types)"
echo "12. Protein neighborhood analysis"
echo "13. Error handling (invalid parameters)"
echo "14. Complex filtering combinations"
echo "15. Performance testing (large datasets)"

echo -e "\n${YELLOW}Note: Make sure the Django server is running before executing these tests!${NC}"
echo "Run: cd dataportal_api && python manage.py runserver"



# Basic interactions
curl -X GET "http://localhost:8000/api/ppi/interactions"

# With species filter
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV"

# With pagination
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&page=1&per_page=10"

# DS score >= 0.8
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=ds_score&score_threshold=0.8&per_page=5"

# String score >= 0.7
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&score_type=string_score&score_threshold=0.7&per_page=5"

# XL-MS evidence
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&has_xlms=true&per_page=5"

# STRING evidence
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&has_string=true&per_page=5"

# Network properties
curl -X GET "http://localhost:8000/api/ppi/network-properties?score_type=ds_score&score_threshold=0.8&species_acronym=PV"

# Network data
curl -X GET "http://localhost:8000/api/ppi/network/ds_score?score_threshold=0.8&species_acronym=PV"

# Pretty print responses
curl -X GET "http://localhost:8000/api/ppi/scores/available" | jq '.'
curl -X GET "http://localhost:8000/api/ppi/interactions?species_acronym=PV&per_page=3" | jq '.'