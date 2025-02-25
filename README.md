# backup-database

## How to setup

#### docker compose 
```yml
services:
  db:
    image: mysql:9
    restart: always
    environment:
      MYSQL_DATABASE: exampledb
      MYSQL_USER: exampleuser
      MYSQL_PASSWORD: examplepass
      MYSQL_ROOT_PASSWORD: examplerootpass

  backup-database:
    image: ghcr.io/arsalanses/backup-database:${TAG:-latest}
    restart: unless-stopped
    environment:
      - DB_HOST=db
      - DB_NAME=exampledb
      - DB_USER=exampleuser
      - DB_PASSWORD=examplepass
      - BACKUP_DIR=/backups
      - LOCAL_RETENTION_DAYS=7

      - UPLOAD_TO_S3=false
      - S3_BUCKET=your-s3-bucket
      - AWS_ACCESS_KEY=your-aws-access-key
      - AWS_SECRET_KEY=your-aws-secret-key

      # - WEBHOOK_URL=https://your-webhook-url.com

      - "CRON_SCHEDULE=0 * * * *"
    volume:
      - ./backups:/backups
    logging:
      options:
        max-size: "10m"
```

#### Webhook

example:
- [Gatus external-endpoints](https://github.com/TwiN/gatus/tree/master#external-endpoints)

gatus config:
```yml
external-endpoints:
  - name: webhook
    group: database
    token: "database"
    alerts:
      - type: telegram
        send-on-resolved: true
```
