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
    echo "MONGODB_URL=your_mongodb_url"
    echo "MONGODB_DB_NAME=scopelabs"
    echo "SUPABASE_URL=your_supabase_url"
    echo "SUPABASE_KEY=your_supabase_anon_key"
    echo "SUPABASE_SERVICE_KEY=your_supabase_service_key"
    echo "POSTGRES_URI=your_postgres_connection_string"
    exit 1
fi

# Source the .env file to load environment variables
echo "Loading environment variables..."
source .env

# Verify critical environment variables are loaded
if [ -z "$POSTGRES_URI" ]; then
    echo "Error: POSTGRES_URI not loaded from .env file"
    exit 1
fi

echo "✅ Environment variables loaded successfully"

# Run database migrations
echo "Running database migrations..."
python3.9 scripts/run_migrations.py --execute

# Check if migrations were successful
if [ $? -ne 0 ]; then
    echo "Error: Database migrations failed. Please check the logs and fix any issues."
    exit 1
fi

# Run Docker container with .env file
echo "Starting Docker container..."
docker run -p 8000:8000 \
    --env-file .env \
    seo-scraper

echo "Server is running at http://localhost:8000" 