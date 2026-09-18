# PPI Use Case - API Version

This directory contains the updated PPI use case notebook that uses the METT Data Portal API instead of local CSV files.

## Files

- `ppi_use_case.ipynb` - Updated Jupyter notebook using API calls
- `utils_api.py` - API client utilities for PPI data access
- `utils.py` - Original utilities (for reference)
- `test_api.py` - Test script to verify API endpoints
- `README_API.md` - This file

## Prerequisites

1. **Django API Server**: The METT Data Portal API must be running
   ```bash
   cd dataportal_api
   source set-env-dev.sh  # Set environment variables
   python manage.py runserver
   ```

2. **PPI Data**: The PPI index must be populated with data
   ```bash
   cd dataportal_api
   python manage.py import_ppi_with_genes --folder /path/to/ppi/data
   ```

3. **Python Dependencies**: Install required packages
   ```bash
   pip install requests pandas numpy networkx matplotlib seaborn adjustText
   ```

## Usage

### 1. Test API Connection

Before running the notebook, test that the API is working:

```bash
python test_api.py
```

This will test all PPI API endpoints and verify they're working correctly.

### 2. Run the Notebook

1. Start Jupyter notebook:
   ```bash
   jupyter notebook ppi_use_case.ipynb
   ```

2. Update API configuration if needed:
   - Edit `utils_api.py` and change `API_BASE_URL` if your API is running on a different host/port

3. Run the notebook cells in order

## API Endpoints Used

The notebook uses the following API endpoints:

- `GET /api/ppi/interactions` - Search PPI interactions with filtering
- `GET /api/ppi/network-properties` - Get network statistics
- `GET /api/ppi/network/{score_type}` - Get network data
- `GET /api/ppi/neighborhood/{protein_id}` - Get protein neighborhood

## Key Changes from Original

1. **Data Source**: Uses API instead of CSV files
2. **Real-time Data**: Always gets the latest data from Elasticsearch
3. **Flexible Filtering**: Can easily change species, score types, thresholds
4. **Scalable**: Handles large datasets through pagination
5. **Error Handling**: Graceful fallback to local calculations if API fails

## Configuration

### API Base URL
Update the `API_BASE_URL` in `utils_api.py` if your API is running on a different host:

```python
API_BASE_URL = "http://your-api-host:8000/api"
```

### Species
Change the species by updating the `species_acronym` variable in the notebook:

```python
species_acronym = 'BU'  # For Bacteroides uniformis
species_acronym = 'PV'  # For Phocaeicola vulgatus
```

## Troubleshooting

### API Connection Issues
- Verify the Django server is running: `python manage.py runserver`
- Check the API_BASE_URL is correct
- Test with `python test_api.py`

### Data Issues
- Ensure PPI data is imported: `python manage.py import_ppi_with_genes`
- Check Elasticsearch is running and accessible
- Verify the PPI index exists and has data

### Performance Issues
- Reduce `per_page` parameter for large datasets
- Use specific score filters to reduce data volume
- Consider using pagination for very large result sets

## Benefits of API Approach

1. **Always Up-to-Date**: No need to manually update CSV files
2. **Flexible**: Easy to change parameters without regenerating files
3. **Scalable**: Can handle much larger datasets
4. **Consistent**: Same data source as the web portal
5. **Maintainable**: Centralized data management
