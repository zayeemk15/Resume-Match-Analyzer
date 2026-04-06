"""
conftest.py — Add project root to sys.path so 'backend.*' imports work in tests.
"""
import sys
from pathlib import Path

# Ensure project root (directory containing 'backend/') is on the path
sys.path.insert(0, str(Path(__file__).parent))
