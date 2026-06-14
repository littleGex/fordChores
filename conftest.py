import os
import sys

# Make the "chores" package importable when running pytest from the repo
# root (e.g. `python -m pytest tests/test_payout.py`).
#
# `from chores import create_app` requires the *parent* of the chores/
# package (i.e. this repo root) to be on sys.path. pytest's rootdir is
# already the repo root when this conftest.py lives here, but we add it
# explicitly to be safe regardless of invocation directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
