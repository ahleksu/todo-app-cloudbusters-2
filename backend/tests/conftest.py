"""Pytest configuration — adds the backend dir to sys.path so tests can import top-level modules."""

import os
import sys

# Add backend/ to sys.path so `from services...`, `from models import ...` etc. work.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
