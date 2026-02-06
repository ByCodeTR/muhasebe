#!/bin/bash
# Render build script for backend

set -e

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database (if needed)..."
python -c "from app.seed import seed_database; import asyncio; asyncio.run(seed_database())" || true

echo "Build complete!"
