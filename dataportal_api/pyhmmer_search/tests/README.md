# PyHMMER Integration Tests

This directory contains comprehensive integration tests for the PyHMMER functionality in the METT DataPortal. These tests verify that the entire search-to-results pipeline works correctly, including API endpoints, data processing, and workflow integration.

## 🧪 Test Overview

### Test Types

1. **Integration Tests** - Test actual functionality end-to-end
2. **API Tests** - Test REST API endpoints and responses
3. **Workflow Tests** - Test complete search workflows
4. **Unit Tests** - Test individual components in isolation

### Test Coverage

- ✅ **Search API** - Job creation, validation, parameter handling
- ✅ **Results API** - Result retrieval, pagination, filtering
- ✅ **Workflow Integration** - Complete search-to-results pipeline
- ✅ **Data Processing** - Domain counting, significance calculation
- ✅ **Error Handling** - Invalid inputs, edge cases, error responses
- ✅ **Performance** - Response times, concurrent access
- ✅ **Authentication** - User authentication and authorization

## 🚀 Quick Start

### Prerequisites

1. **Django Environment** - Ensure Django is properly configured
2. **Database** - Test database should be accessible
3. **Dependencies** - All required packages installed
4. **Environment Variables** - Set up as per `set-env-dev.sh`

### Running Tests

#### Option 1: Using the Test Runner Script (Recommended)

```bash
# Navigate to the dataportal_api directory
cd dataportal_api

# Run all integration tests
python pyhmmer_search/run_integration_tests.py --all

# Run specific test suites
python pyhmmer_search/run_integration_tests.py --search --verbose
python pyhmmer_search/run_integration_tests.py --results --coverage
python pyhmmer_search/run_integration_tests.py --workflow

# Run with coverage and parallel execution
python pyhmmer_search/run_integration_tests.py --all --coverage --parallel
```

#### Option 2: Using pytest directly

```bash
# Navigate to the dataportal_api directory
cd dataportal_api

# Run all tests
python -m pytest pyhmmer_search/tests/ -v

# Run specific test files
python -m pytest pyhmmer_search/tests/test_integration_search.py -v
python -m pytest pyhmmer_search/tests/test_integration_results.py -v
python -m pytest pyhmmer_search/tests/test_integration_workflow.py -v

# Run with coverage
python -m pytest pyhmmer_search/tests/ --cov=pyhmmer_search --cov-report=html
```

#### Option 3: Using Django's test runner

```bash
# Navigate to the dataportal_api directory
cd dataportal_api

# Run all tests
python manage.py test pyhmmer_search.tests

# Run specific test classes
python manage.py test pyhmmer_search.tests.test_integration_search.TestPyhmmerSearchIntegration
```

## 📁 Test Structure

```
pyhmmer_search/tests/
├── conftest.py                          # Pytest configuration and fixtures
├── test_integration_search.py           # Search API integration tests
├── test_integration_results.py          # Results API integration tests
├── test_integration_workflow.py         # Complete workflow tests
└── README.md                            # This file
```

### Test Files Description

#### `conftest.py`
- **Purpose**: Pytest configuration and shared fixtures
- **Contains**: Database setup, user authentication, mock data
- **Usage**: Automatically loaded by pytest

#### `test_integration_search.py`
- **Purpose**: Test search API functionality
- **Tests**: Job creation, validation, parameter handling
- **Coverage**: Search endpoints, job lifecycle, error handling

#### `test_integration_results.py`
- **Purpose**: Test results API functionality
- **Tests**: Result retrieval, pagination, filtering, sorting
- **Coverage**: Results endpoints, data processing, performance

#### `test_integration_workflow.py`
- **Purpose**: Test complete search workflows
- **Tests**: End-to-end pipeline, integration points, edge cases
- **Coverage**: Complete workflow, concurrent access, data persistence

## 🔧 Test Configuration

### Environment Setup

The tests use the Django test framework and automatically:
- Create test database
- Set up test users
- Create test databases
- Clean up after each test

### Fixtures

Common test fixtures are defined in `conftest.py`:

- `authenticated_client` - API client with authenticated user
- `test_database` - Test database for searches
- `sample_search_request` - Sample search request data
- `mock_pyhmmer_results` - Mock search results for testing

### Test Data

Tests use realistic but minimal data:
- **Sequences**: Short protein sequences for testing
- **Parameters**: Valid PyHMMER parameters
- **Databases**: Mock database references
- **Users**: Test user accounts

## 📊 Test Scenarios

### Search API Tests

1. **Job Creation**
   - Valid search requests
   - Parameter validation
   - Database validation
   - Authentication requirements

2. **Job Lifecycle**
   - Job status transitions
   - Task execution
   - Result generation
   - Error handling

3. **Parameter Validation**
   - E-value vs Bit Score thresholds
   - Parameter relationships
   - Invalid inputs
   - Edge cases

### Results API Tests

1. **Result Retrieval**
   - Successful result fetching
   - Pagination
   - Filtering
   - Sorting

2. **Data Structure**
   - Result format validation
   - Domain information
   - Significance calculations
   - Field completeness

3. **Performance**
   - Response times
   - Concurrent access
   - Large datasets
   - Memory usage

### Workflow Tests

1. **Complete Pipeline**
   - Search → Execution → Results
   - Data persistence
   - State management
   - Integration points

2. **Edge Cases**
   - Empty sequences
   - Very long sequences
   - Special characters
   - Boundary conditions

3. **Error Scenarios**
   - Invalid databases
   - Network failures
   - Timeout conditions
   - Resource constraints

## 🎯 Running Specific Tests

### By Test Name

```bash
# Run tests with specific names
python -m pytest pyhmmer_search/tests/ -k "test_search_api" -v

# Run tests matching patterns
python -m pytest pyhmmer_search/tests/ -k "validation" -v
python -m pytest pyhmmer_search/tests/ -k "workflow" -v
```

### By Test Class

```bash
# Run specific test class
python -m pytest pyhmmer_search/tests/test_integration_search.py::TestPyhmmerSearchIntegration -v

# Run specific test method
python -m pytest pyhmmer_search/tests/test_integration_search.py::TestPyhmmerSearchIntegration::test_search_api_endpoint_creation -v
```

### By Markers

```bash
# Run tests with specific markers
python -m pytest pyhmmer_search/tests/ -m "integration" -v
python -m pytest pyhmmer_search/tests/ -m "api" -v
python -m pytest pyhmmer_search/tests/ -m "workflow" -v
python -m pytest pyhmmer_search/tests/ -m "slow" -v
```

## 📈 Coverage and Reporting

### Generate Coverage Report

```bash
# Run tests with coverage
python -m pytest pyhmmer_search/tests/ --cov=pyhmmer_search --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html
```

### Coverage Targets

The tests aim for:
- **Line Coverage**: >90%
- **Branch Coverage**: >80%
- **Function Coverage**: >95%

## 🐛 Debugging Tests

### Verbose Output

```bash
# Enable verbose output
python -m pytest pyhmmer_search/tests/ -v -s

# Show full traceback
python -m pytest pyhmmer_search/tests/ --tb=long
```

### Debug Mode

```bash
# Run with debugger
python -m pytest pyhmmer_search/tests/ --pdb

# Run specific failing test
python -m pytest pyhmmer_search/tests/test_integration_search.py::test_search_api_endpoint_creation --pdb
```

### Logging

Tests include comprehensive logging:
- Test setup and teardown
- API requests and responses
- Database operations
- Error conditions

## 🔄 Continuous Integration

### CI Configuration

These tests are designed to run in CI environments:
- **Database**: Uses test database
- **Dependencies**: Minimal external requirements
- **Isolation**: Tests don't interfere with each other
- **Cleanup**: Automatic cleanup after each test

### Running in CI

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest pyhmmer_search/tests/ --cov=pyhmmer_search --cov-report=xml

# Generate coverage report
coverage xml
```

## 📝 Adding New Tests

### Test Structure

```python
def test_new_functionality(self):
    """Test description of what is being tested."""
    # Arrange - Set up test data
    test_data = {...}
    
    # Act - Execute the functionality
    result = function_under_test(test_data)
    
    # Assert - Verify the results
    self.assertEqual(result.status_code, 200)
    self.assertIn('expected_field', result.data)
```

### Test Naming Convention

- **Test methods**: `test_<functionality>_<scenario>`
- **Test classes**: `Test<Component><Type>`
- **Test files**: `test_<type>_<component>.py`

### Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Always clean up test data
3. **Descriptive**: Test names should be clear
4. **Comprehensive**: Cover success and failure cases
5. **Realistic**: Use realistic test data

## 🚨 Common Issues

### Database Connection

```bash
# Error: Database connection failed
# Solution: Ensure test database is accessible
python manage.py migrate --run-syncdb
```

### Import Errors

```bash
# Error: Module not found
# Solution: Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:/path/to/mett-dataportal/dataportal_api"
```

### Authentication Issues

```bash
# Error: User authentication failed
# Solution: Tests automatically create test users
# Ensure Django auth is properly configured
```

## 📚 Additional Resources

- **Django Testing**: https://docs.djangoproject.com/en/stable/topics/testing/
- **Pytest**: https://docs.pytest.org/
- **REST Framework Testing**: https://www.django-rest-framework.org/api-guide/testing/
- **PyHMMER Documentation**: https://pyhmmer.readthedocs.io/

## 🤝 Contributing

When adding new tests:

1. **Follow existing patterns** - Use similar structure and naming
2. **Add comprehensive coverage** - Test success and failure cases
3. **Update documentation** - Document new test scenarios
4. **Maintain isolation** - Ensure tests don't interfere with each other
5. **Add appropriate markers** - Mark tests with relevant pytest markers

## 📞 Support

For questions about the integration tests:

1. **Check this README** - Most common questions are answered here
2. **Review test code** - Tests serve as examples of proper usage
3. **Check test output** - Verbose output often reveals the issue
4. **Review Django logs** - Check for database or configuration issues

---

**Happy Testing! 🧪✨**
