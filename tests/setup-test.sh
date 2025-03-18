#!/bin/bash
# setup-test.sh
# This script sets up a virtual environment for testing the integration,
# installs the required dependencies, and runs the tests.

set -e

# echo "Setting up virtual environment for testing..."
# python3 -m venv venv
# source venv/bin/activate

# echo "Upgrading pip..."
# pip install --upgrade pip

# echo "Installing test dependencies..."
# pip install pytest homeassistant

echo "Running tests..."
pytest --maxfail=1 --disable-warnings -q tests/test_integration.py 
