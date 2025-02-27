# backup-database

## How to setup

#### docker compose 
```yml
services:
  mysql:
    image: mysql:9
    restart: always
    environment:
      MYSQL_DATABASE: exampledb
      MYSQL_USER: exampleuser
      MYSQL_PASSWORD: examplepass
      MYSQL_ROOT_PASSWORD: examplerootpass

  docker-backup-mysql:
    image: ghcr.io/arsalanses/docker-backup-mysql:${TAG:-latest}
    restart: unless-stopped
    environment:
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_NAME=exampledb
      - DB_USER=root
      - DB_PASSWORD=examplerootpass
      - BACKUP_DIR=/backups

      - UPLOAD_TO_S3=false
      - AWS_ENDPOINT_URL=https://minio-api.example.com
      - S3_BUCKET=your-s3-bucket
      - S3_PREFIX=db-backups
      - AWS_ACCESS_KEY=your-aws-access-key
      - AWS_SECRET_KEY=your-aws-secret-key

      # - WEBHOOK_URL=https://your-webhook-url.com/api/v1/endpoints/database_webhook/external
      - BEARER_TOKEN=database

      - LOCAL_RETENTION_DAYS=7
      - "CRON_SCHEDULE=0 * * * *"
    volumes:
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
