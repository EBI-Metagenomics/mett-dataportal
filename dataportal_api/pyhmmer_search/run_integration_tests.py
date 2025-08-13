#!/usr/bin/env python3
"""
PyHMMER Integration Test Runner

This script runs comprehensive integration tests for the PyHMMER functionality.
It can run different test suites and provide detailed output.

Usage:
    python run_integration_tests.py [options]

Options:
    --all              Run all integration tests
    --search           Run search API integration tests only
    --results          Run results API integration tests only
    --workflow         Run workflow integration tests only
    --unit             Run unit tests only
    --verbose          Verbose output
    --coverage         Run with coverage reporting
    --parallel         Run tests in parallel (if supported)
    --help             Show this help message
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

# Add the project root to the Python path
# We need to go up two levels: pyhmmer_search -> dataportal_api -> project_root
current_dir = Path(__file__).parent
dataportal_api_dir = current_dir.parent
project_root = dataportal_api_dir.parent

# Add both paths to ensure imports work
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dataportal_api_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dataportal.settings')

# Import Django and set it up
try:
    import django
    django.setup()
    print(f"✅ Django configured successfully")
    print(f"✅ Project root: {project_root}")
    print(f"✅ Dataportal API dir: {dataportal_api_dir}")
except Exception as e:
    print(f"❌ Django configuration failed: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

def run_command(cmd, description, verbose=False):
    """Run a command and handle errors."""
    if verbose:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if verbose:
            print("STDOUT:")
            print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
        
        return True, result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {description}:")
        print(f"Command: {' '.join(cmd)}")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False, e.stderr

def run_pytest_tests(test_path, description, verbose=False, coverage=False, parallel=False):
    """Run pytest tests with the given options."""
    cmd = ["python", "-m", "pytest", test_path, "-v"]
    
    if coverage:
        cmd.extend(["--cov=pyhmmer_search", "--cov-report=html", "--cov-report=term"])
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    if verbose:
        cmd.append("--tb=long")
    else:
        cmd.append("--tb=short")
    
    return run_command(cmd, description, verbose)

def run_django_tests(test_path, description, verbose=False):
    """Run Django tests with the given options."""
    cmd = ["python", "manage.py", "test", test_path, "--verbosity=2"]
    
    if verbose:
        cmd.append("--verbosity=3")
    
    return run_command(cmd, description, verbose)

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest is not available. Install with: pip install pytest")
        return False
    
    # Check if Django is properly configured
    try:
        from django.conf import settings
        print("✅ Django is properly configured")
    except Exception as e:
        print(f"❌ Django configuration error: {e}")
        return False
    
    # Check if PyHMMER models are available
    try:
        from pyhmmer_search.search.models import HmmerJob, Database
        print("✅ PyHMMER models are available")
    except Exception as e:
        print(f"❌ PyHMMER models error: {e}")
        return False
    
    print("✅ All dependencies are available\n")
    return True

def run_search_integration_tests(verbose=False, coverage=False):
    """Run search API integration tests."""
    print("🚀 Running Search API Integration Tests...")
    
    test_path = "pyhmmer_search/tests/test_integration_search.py"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "Search API Integration Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ Search API Integration Tests completed successfully")
        else:
            print("❌ Search API Integration Tests failed")
        
        return success
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def run_results_integration_tests(verbose=False, coverage=False):
    """Run results API integration tests."""
    print("🚀 Running Results API Integration Tests...")
    
    test_path = "pyhmmer_search/tests/test_integration_results.py"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "Results API Integration Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ Results API Integration Tests completed successfully")
        else:
            print("❌ Results API Integration Tests failed")
        
        return success
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def run_workflow_integration_tests(verbose=False, coverage=False):
    """Run workflow integration tests."""
    print("🚀 Running Workflow Integration Tests...")
    
    test_path = "pyhmmer_search/tests/test_integration_workflow.py"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "Workflow Integration Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ Workflow Integration Tests completed successfully")
        else:
            print("❌ Workflow Integration Tests failed")
        
        return success
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    print("🚀 Running Unit Tests...")
    
    test_path = "pyhmmer_search/search/test_tasks.py"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "Unit Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ Unit Tests completed successfully")
        else:
            print("❌ Unit Tests failed")
        
        return success
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def run_all_tests(verbose=False, coverage=False, parallel=False):
    """Run all tests."""
    print("🚀 Running All Tests...")
    
    test_path = "pyhmmer_search/tests/"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "All Integration Tests", 
            verbose, 
            coverage,
            parallel
        )
        
        if success:
            print("✅ All Tests completed successfully")
        else:
            print("❌ All Tests failed")
        
        return success
    else:
        print(f"❌ Test directory not found: {test_path}")
        return False

def main():
    """Main function to run the test suite."""
    parser = argparse.ArgumentParser(
        description="PyHMMER Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_integration_tests.py --all                    # Run all tests
    python run_integration_tests.py --search --verbose       # Run search tests with verbose output
    python run_integration_tests.py --results --coverage     # Run results tests with coverage
    python run_integration_tests.py --workflow               # Run workflow tests only
        """
    )
    
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all integration tests"
    )
    parser.add_argument(
        "--search", 
        action="store_true", 
        help="Run search API integration tests only"
    )
    parser.add_argument(
        "--results", 
        action="store_true", 
        help="Run results API integration tests only"
    )
    parser.add_argument(
        "--workflow", 
        action="store_true", 
        help="Run workflow integration tests only"
    )
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run unit tests only"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--parallel", 
        action="store_true", 
        help="Run tests in parallel (if supported)"
    )
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all tests
    if not any([args.all, args.search, args.results, args.workflow, args.unit]):
        args.all = True
    
    print("🧪 PyHMMER Integration Test Runner")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Dependency check failed. Please fix the issues above.")
        sys.exit(1)
    
    start_time = time.time()
    results = []
    
    try:
        # Run the requested tests
        if args.all:
            results.append(("All Tests", run_all_tests(args.verbose, args.coverage, args.parallel)))
        else:
            if args.search:
                results.append(("Search API Tests", run_search_integration_tests(args.verbose, args.coverage)))
            
            if args.results:
                results.append(("Results API Tests", run_results_integration_tests(args.verbose, args.coverage)))
            
            if args.workflow:
                results.append(("Workflow Tests", run_workflow_integration_tests(args.verbose, args.coverage)))
            
            if args.unit:
                results.append(("Unit Tests", run_unit_tests(args.verbose, args.coverage)))
        
        # Print summary
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        all_passed = True
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name}: {status}")
            if not success:
                all_passed = False
        
        print(f"\n⏱️  Total time: {total_time:.2f} seconds")
        
        if all_passed:
            print("\n🎉 All tests passed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed. Please check the output above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
