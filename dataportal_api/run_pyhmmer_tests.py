#!/usr/bin/env python3
"""
PyHMMER Test Runner (from dataportal_api directory)

This script runs PyHMMER tests from the dataportal_api directory.
It's simpler and more reliable than running from subdirectories.

Usage:
    python run_pyhmmer_tests.py [options]

Options:
    --all              Run all PyHMMER tests
    --integration      Run integration tests only
    --unit             Run unit tests only
    --search           Run search API tests only
    --results          Run results API tests only
    --workflow         Run workflow tests only
    --verbose          Verbose output
    --coverage         Run with coverage reporting
    --help             Show this help message
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

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

def run_pytest_tests(test_path, description, verbose=False, coverage=False):
    """Run pytest tests with the given options."""
    cmd = ["python", "-m", "pytest", test_path, "-v"]
    
    if coverage:
        cmd.extend(["--cov=pyhmmer_search", "--cov-report=html", "--cov-report=term"])
    
    if verbose:
        cmd.append("--tb=long")
    else:
        cmd.append("--tb=short")
    
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
    
    # Check if we're in the right directory
    if not os.path.exists("manage.py"):
        print("❌ manage.py not found. Please run this script from the dataportal_api directory.")
        return False
    
    print("✅ Running from correct directory (dataportal_api)")
    print("✅ All dependencies are available\n")
    return True

def run_integration_tests(verbose=False, coverage=False):
    """Run PyHMMER integration tests."""
    print("🚀 Running PyHMMER Integration Tests...")
    
    test_path = "pyhmmer_search/tests/"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "PyHMMER Integration Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ PyHMMER Integration Tests completed successfully")
        else:
            print("❌ PyHMMER Integration Tests failed")
        
        return success
    else:
        print(f"❌ Test directory not found: {test_path}")
        return False

def run_unit_tests(verbose=False, coverage=False):
    """Run PyHMMER unit tests."""
    print("🚀 Running PyHMMER Unit Tests...")
    
    test_path = "pyhmmer_search/search/test_tasks.py"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "PyHMMER Unit Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ PyHMMER Unit Tests completed successfully")
        else:
            print("❌ PyHMMER Unit Tests failed")
        
        return success
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def run_search_tests(verbose=False, coverage=False):
    """Run PyHMMER search API tests."""
    print("🚀 Running PyHMMER Search API Tests...")
    
    test_path = "pyhmmer_search/tests/test_integration_search.py"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "PyHMMER Search API Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ PyHMMER Search API Tests completed successfully")
        else:
            print("❌ PyHMMER Search API Tests failed")
        
        return success
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def run_results_tests(verbose=False, coverage=False):
    """Run PyHMMER results API tests."""
    print("🚀 Running PyHMMER Results API Tests...")
    
    test_path = "pyhmmer_search/tests/test_integration_results.py"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "PyHMMER Results API Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ PyHMMER Results API Tests completed successfully")
        else:
            print("❌ PyHMMER Results API Tests failed")
        
        return success
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def run_workflow_tests(verbose=False, coverage=False):
    """Run PyHMMER workflow tests."""
    print("🚀 Running PyHMMER Workflow Tests...")
    
    test_path = "pyhmmer_search/tests/test_integration_workflow.py"
    
    if os.path.exists(test_path):
        success, output = run_pytest_tests(
            test_path, 
            "PyHMMER Workflow Tests", 
            verbose, 
            coverage
        )
        
        if success:
            print("✅ PyHMMER Workflow Tests completed successfully")
        else:
            print("❌ PyHMMER Workflow Tests failed")
        
        return success
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def main():
    """Main function to run the test suite."""
    parser = argparse.ArgumentParser(
        description="PyHMMER Test Runner (from dataportal_api directory)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_pyhmmer_tests.py --all                    # Run all tests
    python run_pyhmmer_tests.py --integration --verbose  # Run integration tests with verbose output
    python run_pyhmmer_tests.py --search --coverage      # Run search tests with coverage
    python run_pyhmmer_tests.py --workflow               # Run workflow tests only
        """
    )
    
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all PyHMMER tests"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run integration tests only"
    )
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run unit tests only"
    )
    parser.add_argument(
        "--search", 
        action="store_true", 
        help="Run search API tests only"
    )
    parser.add_argument(
        "--results", 
        action="store_true", 
        help="Run results API tests only"
    )
    parser.add_argument(
        "--workflow", 
        action="store_true", 
        help="Run workflow tests only"
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
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all tests
    if not any([args.all, args.integration, args.unit, args.search, args.results, args.workflow]):
        args.all = True
    
    print("🧪 PyHMMER Test Runner (from dataportal_api directory)")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Dependency check failed. Please fix the issues above.")
        sys.exit(1)
    
    start_time = time.time()
    results = []
    
    try:
        # Run the requested tests
        if args.all:
            results.append(("All PyHMMER Tests", run_integration_tests(args.verbose, args.coverage)))
        else:
            if args.integration:
                results.append(("Integration Tests", run_integration_tests(args.verbose, args.coverage)))
            
            if args.unit:
                results.append(("Unit Tests", run_unit_tests(args.verbose, args.coverage)))
            
            if args.search:
                results.append(("Search API Tests", run_search_tests(args.verbose, args.coverage)))
            
            if args.results:
                results.append(("Results API Tests", run_results_tests(args.verbose, args.coverage)))
            
            if args.workflow:
                results.append(("Workflow Tests", run_workflow_tests(args.verbose, args.coverage)))
        
        # Print summary
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
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
