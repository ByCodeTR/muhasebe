#!/bin/bash
# PostgreSQL restore script for Muhasebe database

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh /var/backups/muhasebe/${DB_NAME:-muhasebe}_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="${DB_NAME:-muhasebe}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "[$(date)] Restoring $DB_NAME from $BACKUP_FILE..."
echo "WARNING: This will DROP and recreate the database!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Restore
if [ -n "$DATABASE_URL" ]; then
    # Drop and recreate (requires superuser)
    echo "Dropping existing data..."
    psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    
    echo "Restoring from backup..."
    gunzip -c "$BACKUP_FILE" | psql "$DATABASE_URL"
else
    PGHOST="${PGHOST:-localhost}"
    PGPORT="${PGPORT:-5432}"
    PGUSER="${PGUSER:-postgres}"
    
    echo "Dropping existing data..."
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    
    echo "Restoring from backup..."
    gunzip -c "$BACKUP_FILE" | psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$DB_NAME"
fi

echo "[$(date)] Restore completed successfully!"
