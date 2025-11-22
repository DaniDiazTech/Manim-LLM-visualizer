#!/bin/bash
# Setup script for traditional venv approach

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing package and dependencies..."
pip install -e .

echo ""
echo "✓ Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To start the API server, run:"
echo "  manim-api"
echo "  # or"
echo "  python -m manim_generator.api_server"
echo ""

