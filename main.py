import os
import subprocess
import boto3
from botocore.exceptions import NoCredentialsError
import requests
from datetime import datetime, timedelta
import logging
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
BACKUP_DIR = os.getenv('BACKUP_DIR', '/tmp')
UPLOAD_TO_S3 = os.getenv('UPLOAD_TO_S3', 'false').lower() == 'true'
S3_BUCKET = os.getenv('S3_BUCKET')
S3_PREFIX = os.getenv('S3_PREFIX', 'backups')
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
LOCAL_RETENTION_DAYS = int(os.getenv('LOCAL_RETENTION_DAYS', '7'))

def backup_mysql():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'{DB_NAME}_backup_{timestamp}.sql')

    try:
        command = [
            'mysqldump',
            f'-h{DB_HOST}',
            f'-P{DB_PORT}',
            f'-u{DB_USER}',
            f'-p{DB_PASSWORD}',
            '--opt',
            DB_NAME,
            '--result-file', backup_file
        ]

        subprocess.run(command, check=True)
        logger.info(f"Backup successful: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")
        return None

def upload_to_s3(file_path):
    if not UPLOAD_TO_S3:
        logger.info("S3 upload is disabled (UPLOAD_TO_S3 is not set to 'true')")
        return True

    if not all([S3_BUCKET, AWS_ACCESS_KEY, AWS_SECRET_KEY]):
        logger.error("S3 upload is enabled but missing required S3 configuration (S3_BUCKET, AWS_ACCESS_KEY, AWS_SECRET_KEY)")
        return False

    s3_client = boto3.client(
        's3',
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    s3_key = f"{S3_PREFIX}/{os.path.basename(file_path)}"

    try:
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)
        logger.info(f"Upload successful: s3://{S3_BUCKET}/{s3_key}")
        return True
    except FileNotFoundError:
        logger.error("The file was not found")
        return False
    except NoCredentialsError:
        logger.error("Credentials not available")
        return False

def call_webhook(success, backup_file, s3_key=None):
    if not WEBHOOK_URL:
        logger.warning("Webhook URL not provided, skipping webhook call")
        return

    query_params = {
        'success': 'true' if success else 'false',
        'error': 'true' if not success else 'false'
    }

    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(WEBHOOK_URL, params=query_params, headers=headers)
        response.raise_for_status()
        logger.info("Webhook called successfully")
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook call failed: {e}")

def cleanup_old_backups():
    """Delete backup files older than LOCAL_RETENTION_DAYS."""
    if LOCAL_RETENTION_DAYS <= 0:
        logger.info("Local retention is disabled (LOCAL_RETENTION_DAYS <= 0)")
        return

    now = datetime.now()
    cutoff_time = now - timedelta(days=LOCAL_RETENTION_DAYS)

    backup_files = glob.glob(os.path.join(BACKUP_DIR, f'{DB_NAME}_backup_*.sql'))

    for backup_file in backup_files:
        file_creation_time = datetime.fromtimestamp(os.path.getctime(backup_file))
        if file_creation_time < cutoff_time:
            try:
                os.remove(backup_file)
                logger.info(f"Deleted old backup file: {backup_file}")
            except OSError as e:
                logger.error(f"Failed to delete old backup file {backup_file}: {e}")

def main():
    cleanup_old_backups()

    backup_file = backup_mysql()

    if backup_file:
        upload_success = upload_to_s3(backup_file)
        s3_key = f"{S3_PREFIX}/{os.path.basename(backup_file)}" if upload_success and UPLOAD_TO_S3 else None
        call_webhook(upload_success, backup_file, s3_key)
    # else:
    #     call_webhook(False, None)

if __name__ == "__main__":
    main()
