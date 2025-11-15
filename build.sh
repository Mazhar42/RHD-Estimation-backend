#!/usr/bin/env bash
set -euo pipefail

# Ensure we run from backend directory
cd "$(dirname "$0")"

echo "Installing Python dependencies..."
python --version || true
pip install --upgrade pip
pip install -r requirements.txt

echo "Build steps completed."