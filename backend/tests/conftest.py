"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add backend directory to Python path so 'src' can be imported as a package
# This matches how the app runs normally (from backend/ directory)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

