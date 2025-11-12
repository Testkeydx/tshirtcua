#!/bin/bash
# Setup script for SPS Commerce Order Processing Automation

echo "Setting up SPS Commerce Order Processing Automation..."
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create directories
echo "Creating input and output directories..."
mkdir -p input output

echo ""
echo "Setup complete!"
echo ""
echo "To use the script:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Place your CSV files in the 'input' directory"
echo "3. Run: python order_processor.py"
echo "4. Check the 'output' directory for results"

