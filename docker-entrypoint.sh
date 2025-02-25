#!/bin/sh
set -e

CRON_SCHEDULE=${CRON_SCHEDULE:-"0 * * * *"}

if [ -z "$CRON_SCHEDULE" ] ; then
  echo "Error: CRON_SCHEDULE environment variables must be set."
  exit 1
fi

echo "$CRON_SCHEDULE python /app/main.py" > /app/crontab

chmod 0644 /app/crontab

mkdir -p $BACKUP_DIR

exec /app/supercronic /app/crontab
