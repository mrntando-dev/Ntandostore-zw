#!/bin/bash

# Simple installation script for Render.com

echo "🚀 Installing Ntandostore..."

# Upgrade pip and install build essentials
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

# Create directories
mkdir -p static/uploads/logos
mkdir -p static/uploads/company
mkdir -p logs

echo "✅ Installation complete!"
