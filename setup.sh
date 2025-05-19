#!/usr/bin/env bash
# Simple setup script for the Digital Garden project

set -euo pipefail

# Use the directory of this script as the project root
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is not installed. Please install it from https://github.com/astral-sh/uv" >&2
    exit 1
fi

# Create the Python virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv venv..."
    uv venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies with uv sync..."
uv sync

# Optionally install Node dependencies if package.json exists
if [ -f package.json ]; then
    echo "Installing Node dependencies with npm install..."
    npm install
fi

echo "Setup complete. Activate the environment with 'source .venv/bin/activate'."
