#!/bin/bash
# PostgreSQL backup script for Muhasebe database
# Run via cron: 0 3 * * * /path/to/backup.sh

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/muhasebe}"
DB_NAME="${DB_NAME:-muhasebe}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup of $DB_NAME..."

# Dump and compress
if [ -n "$DATABASE_URL" ]; then
    # Use DATABASE_URL if available (Render/Heroku style)
    pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"
else
    # Use individual variables
    PGHOST="${PGHOST:-localhost}"
    PGPORT="${PGPORT:-5432}"
    PGUSER="${PGUSER:-postgres}"
    
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$DB_NAME" | gzip > "$BACKUP_FILE"
fi

# Verify backup was created
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] Backup completed: $BACKUP_FILE ($SIZE)"
else
    echo "[$(date)] ERROR: Backup failed!"
    exit 1
fi

# Remove old backups
echo "[$(date)] Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "[$(date)] Current backups:"
ls -lh "$BACKUP_DIR"/${DB_NAME}_*.sql.gz 2>/dev/null || echo "No backups found"

echo "[$(date)] Backup process completed."
