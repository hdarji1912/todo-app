#!/bin/bash
# backup_db.sh

BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

BACKUP_FILE="$BACKUP_DIR/mydb_$(date +%Y%m%d_%H%M%S).sql"

docker exec mysql mysqldump -u admin -padmin mydb > $BACKUP_FILE

echo "✅ Backupfile created successfully: $BACKUP_FILE"