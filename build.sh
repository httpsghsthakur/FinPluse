#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Node.js dependencies and building frontend..."
npm install
npm run build

echo "Installing Python dependencies..."
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
