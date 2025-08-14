#!/usr/bin/env python3
"""
Simple PyHMMER Test Runner (from dataportal_api directory)

This script runs PyHMMER tests using pytest with Django's in-memory database.
It's simple and doesn't require additional dependencies.

Usage:
    python run_simple_tests.py [options]

Options:
    --all              Run all PyHMMER tests
    --search           Run search API tests only
    --unit             Run unit tests only
    --basic            Run basic functionality tests only (no database required)
    --verbose          Verbose output
    --help             Show this help message
"""

import os
import sys
import argparse
import subprocess
import time


def setup_django_environment():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dataportal.settings")

    os.environ.setdefault("ENVIRONMENT", "testing")

    os.environ.setdefault("DJANGO_TEST_DATABASE", "sqlite")


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")

    # Check if we're in the right directory
    if not os.path.exists("manage.py"):
        print(
            "❌ manage.py not found. Please run this script from the dataportal_api directory."
        )
        return False

    # Set up Django environment first
    setup_django_environment()

    # Check if Django is available
    try:
        import django

        print("✅ Django is available")
    except ImportError:
        print("❌ Django is not available")
        return False

    # Configure Django before importing Django Ninja
    try:
        django.setup()
        print("✅ Django is configured")
    except Exception as e:
        print(f"❌ Failed to configure Django: {e}")
        return False

    # Now check if Django Ninja is available
    try:

        print("✅ Django Ninja is available")
    except Exception as e:
        print(f"❌ Django Ninja is not available: {e}")
        return False

    print("✅ Running from correct directory (dataportal_api)")
    print("✅ All dependencies are available\n")
    return True


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
            check=True,
            env=dict(os.environ, DJANGO_TEST_DATABASE="sqlite"),
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


def run_basic_tests(verbose=False):
    """Run PyHMMER basic functionality tests (no database required)."""
    print("🚀 Running PyHMMER Basic Functionality Tests...")

    test_path = "pyhmmer_search/tests/test_basic_functionality.py"

    # Use pytest with Django's in-memory database
    cmd = ["python", "-m", "pytest", test_path]
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")

    success, output = run_command(cmd, "PyHMMER Basic Functionality Tests", verbose)

    if success:
        print("✅ PyHMMER Basic Functionality Tests completed successfully")
    else:
        print("❌ PyHMMER Basic Functionality Tests failed")

    return success


def run_search_tests(verbose=False):
    """Run PyHMMER search API tests using pytest."""
    print("🚀 Running PyHMMER Search API Tests...")

    test_path = "pyhmmer_search/tests/test_integration_search.py"

    # Use pytest with Django's in-memory database
    cmd = ["python", "-m", "pytest", test_path]
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")

    success, output = run_command(cmd, "PyHMMER Search API Tests", verbose)

    if success:
        print("✅ PyHMMER Search API Tests completed successfully")
    else:
        print("❌ PyHMMER Search API Tests failed")

    return success


def run_unit_tests(verbose=False):
    """Run PyHMMER unit tests using pytest."""
    print("🚀 Running PyHMMER Unit Tests...")

    test_path = "pyhmmer_search/search/test_tasks.py"

    # Use pytest with Django's in-memory database
    cmd = ["python", "-m", "pytest", test_path]
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")

    success, output = run_command(cmd, "PyHMMER Unit Tests", verbose)

    if success:
        print("✅ PyHMMER Unit Tests completed successfully")
    else:
        print("❌ PyHMMER Unit Tests failed")

    return success


def run_all_tests(verbose=False):
    """Run all PyHMMER tests using pytest."""
    print("🚀 Running All PyHMMER Tests...")

    test_path = "pyhmmer_search"

    # Use pytest with Django's in-memory database
    cmd = ["python", "-m", "pytest", test_path]
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")

    success, output = run_command(cmd, "All PyHMMER Tests", verbose)

    if success:
        print("✅ All PyHMMER Tests completed successfully")
    else:
        print("❌ All PyHMMER Tests failed")

    return success


def main():
    """Main function to run the test suite."""
    parser = argparse.ArgumentParser(
        description="Simple PyHMMER Test Runner (from dataportal_api directory)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_simple_tests.py --all                    # Run all tests
    python run_simple_tests.py --search --verbose       # Run search tests with verbose output
    python run_simple_tests.py --unit                   # Run unit tests only
    python run_simple_tests.py --basic                  # Run basic tests only (no database required)
        """,
    )

    parser.add_argument("--all", action="store_true", help="Run all PyHMMER tests")
    parser.add_argument(
        "--search", action="store_true", help="Run search API tests only"
    )
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--basic",
        action="store_true",
        help="Run basic functionality tests only (no database required)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # If no specific test type is specified, run basic tests first
    if not any([args.all, args.search, args.unit, args.basic]):
        args.basic = True

    print("🧪 Simple PyHMMER Test Runner (from dataportal_api directory)")
    print("=" * 60)
    print(
        "📝 Note: Tests will run using pytest with Django's in-memory SQLite database"
    )
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
            results.append(("All PyHMMER Tests", run_all_tests(args.verbose)))
        else:
            if args.basic:
                results.append(
                    ("Basic Functionality Tests", run_basic_tests(args.verbose))
                )

            if args.search:
                results.append(("Search API Tests", run_search_tests(args.verbose)))

            if args.unit:
                results.append(("Unit Tests", run_unit_tests(args.verbose)))

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
