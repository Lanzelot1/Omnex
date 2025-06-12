#!/usr/bin/env python3
"""Verify Omnex development setup."""

import sys
import subprocess
from pathlib import Path

def check(condition, message):
    """Print check result."""
    status = "✓" if condition else "✗"
    print(f"{status} {message}")
    return condition

def main():
    """Run setup verification."""
    print("Verifying Omnex setup...\n")
    
    all_good = True
    
    # Python version
    all_good &= check(
        sys.version_info >= (3, 9),
        f"Python {sys.version_info.major}.{sys.version_info.minor} (requires 3.9+)"
    )
    
    # Environment file
    all_good &= check(
        Path(".env").exists(),
        ".env file exists"
    )
    
    # Virtual environment
    all_good &= check(
        hasattr(sys, 'prefix') and 'venv' in sys.prefix,
        "Virtual environment activated"
    )
    
    # Dependencies
    try:
        import fastapi
        import pydantic
        import sqlalchemy
        deps_installed = True
    except ImportError:
        deps_installed = False
    
    all_good &= check(deps_installed, "Python dependencies installed")
    
    # Docker
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        docker_available = True
    except:
        docker_available = False
    
    all_good &= check(docker_available, "Docker available")
    
    # Pre-commit hooks
    all_good &= check(
        Path(".git/hooks/pre-commit").exists(),
        "Pre-commit hooks installed"
    )
    
    if all_good:
        print("\n✓ All checks passed! Ready for development.")
        print("\nStart with: make run")
    else:
        print("\n✗ Setup incomplete. Run: make setup")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())