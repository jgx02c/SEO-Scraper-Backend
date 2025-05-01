#!/bin/bash

# Exit on error
set -e

# Check if Python 3.9 is installed
if ! command -v python3.9 &> /dev/null; then
    echo "Python 3.9 is not installed. Please install Python 3.9 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.9 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

# Build Docker image
echo "Building Docker image..."
docker build -t seo-scraper .

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please create a .env file with the following required variables:"
    echo "MONGO_URL=your_mongodb_url"
    echo "MONGO_DB_NAME=scopelabs"
    echo "POSTGRES_URI=postgresql://username:password@host:port/database"
    echo "SUPABASE_JWT_SECRET=your_supabase_jwt_secret"
    echo "JWT_SECRET_KEY=your_jwt_secret_key"
    exit 1
fi

# Run Docker container with .env file
echo "Starting Docker container..."
docker run -p 8000:8000 \
    --env-file .env \
    seo-scraper

echo "Server is running at http://localhost:8000" 