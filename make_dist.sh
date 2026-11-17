#!/usr/bin/env bash
set -e
python3 -m unittest discover -s tests -p 'test_*.py'
python3 qaskills.py eval
