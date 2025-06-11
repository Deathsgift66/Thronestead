#!/usr/bin/env bash
set -e
python -m venv venv
source venv/bin/activate
pip install -r dev_requirements.txt
pytest "$@"
