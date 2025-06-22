#!/usr/bin/env python3
"""
Development setup script for DiskImage

This script sets up the development environment with all necessary dependencies
and development tools.
"""
import subprocess
import sys
import platform
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(command)}")
    if description:
        print(f"  {description}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error: {e}")
        if e.stderr:
            print(f"  Stderr: {e.stderr.strip()}")
        return False


def setup_development_environment():
    """Set up the development environment."""
    print("Setting up DiskImage development environment...")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print()
    
    # Upgrade pip
    print("1. Upgrading pip...")
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"]):
        print("Failed to upgrade pip")
        return False
    
    # Install requirements
    print("\n2. Installing requirements...")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
        print("Failed to install requirements")
        return False
    
    # Install development tools
    print("\n3. Installing additional development tools...")
    dev_tools = [
        "pytest-cov",  # Coverage reporting
        "pre-commit",  # Git hooks
        "tox",         # Testing across environments
    ]
    
    for tool in dev_tools:
        if not run_command([sys.executable, "-m", "pip", "install", tool]):
            print(f"Warning: Failed to install {tool}")
    
    # Setup pre-commit hooks
    print("\n4. Setting up pre-commit hooks...")
    if not run_command(["pre-commit", "install"]):
        print("Warning: Failed to setup pre-commit hooks")
    
    # Run initial tests
    print("\n5. Running initial tests...")
    if not run_command([sys.executable, "-m", "pytest", "tests/", "-v"]):
        print("Warning: Some tests failed")
    
    # Type checking
    print("\n6. Running type checking...")
    if not run_command(["mypy", "backend/", "cli/", "gui/", "--ignore-missing-imports"]):
        print("Warning: Type checking found issues")
    
    # Code formatting check
    print("\n7. Checking code formatting...")
    if not run_command(["black", "--check", "."]):
        print("Warning: Code formatting issues found. Run 'black .' to fix.")
    
    # Import sorting check
    print("\n8. Checking import sorting...")
    if not run_command(["isort", "--check-only", "--diff", "."]):
        print("Warning: Import sorting issues found. Run 'isort .' to fix.")
    
    print("\n" + "="*60)
    print("Development environment setup complete!")
    print()
    print("Next steps:")
    print("  1. Run tests: python -m pytest tests/")
    print("  2. Format code: black .")
    print("  3. Sort imports: isort .")
    print("  4. Type check: mypy backend/ cli/ gui/")
    print("  5. Run GUI: python main.py")
    print("  6. Run CLI: python main.py --help")
    print("="*60)
    
    return True


def main():
    """Main entry point."""
    if not setup_development_environment():
        sys.exit(1)


if __name__ == "__main__":
    main()
