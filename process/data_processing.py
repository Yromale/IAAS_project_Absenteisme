import os
import csv
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from google.cloud import storage, secretmanager
from flask import Flask
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Create a Secret Manager client
secret_client = secretmanager.SecretManagerServiceClient()

def access_secret_version(secret_id):
    project_id = os.getenv('PROJECT_ID')
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = secret_client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode('UTF-8')

# Retrieve secrets
BUCKET_NAME = access_secret_version('GCS_BUCKET_NAME')
CLOUD_SQL_CONNECTION_NAME = access_secret_version('CLOUD_SQL_CONNECTION_NAME')
DB_USER = access_secret_version('DB_USER')
DB_PASSWORD = access_secret_version('DB_PASSWORD')
DB_NAME = access_secret_version('DB_NAME')

# Create a connection to the Cloud SQL database
DATABASE_URI = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@/{DB_NAME}?host=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
)

engine = create_engine(DATABASE_URI)

app = Flask(__name__)

@app.route('/')
def main():
    start_time = datetime.now()
    created_videos = 0
    updated_videos = 0
    status = "success"

    try:
        channel_filenames = [
            'Outdoor Boys_channel_data.csv',
            'PacificSound3003_channel_data.csv',
            'I did a thing_channel_data.csv'
        ]

        for channel_filename in channel_filenames:
            data = download_from_gcs(channel_filename)
            insert_channel_data_to_sql(data, channel_filename.split('_')[0])

        filenames = [
            'OutdoorBoys_data.csv',
            'pacificsound3003_data.csv',
            'Ididathing_data.csv'
        ]

        for filename in filenames:
            data = download_from_gcs(filename)
            created, updated = insert_data_to_sql(data, filename.split('_')[0])
            created_videos += created
            updated_videos += updated

    except Exception as e:
        status = "failed"
        logging.error(f"Error during data processing: {e}")

    end_time = datetime.now()

    # Insert metadata into ImportTask table
    try:
        insert_import_task(start_time, end_time, created_videos, updated_videos, status)
    except Exception as e:
        logging.error(f"Error inserting import task: {e}")
        status = "failed"

    return "Data processing complete"

# Download a file from GCS
def download_from_gcs(filename):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    data = blob.download_as_string()
    return data.decode('utf-8')

# Insert data into the SQL database
def insert_data_to_sql(data, channel_name):
    conn = engine.connect()
    reader = csv.DictReader(data.splitlines())
    created_videos = 0
    updated_videos = 0
    for row in reader:
        # Count the number of rows before inserting or updating
        count_before = conn.execute(
            text("SELECT COUNT(*) FROM video")
        ).fetchone()[0]

        conn.execute(
            text("""
                INSERT INTO video (video_id, title, description, published_at, likes, views)
                VALUES (:video_id, :title, :description, :published_at, :likes, :views)
                ON CONFLICT (video_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    published_at = EXCLUDED.published_at,
                    likes = EXCLUDED.likes,
                    views = EXCLUDED.views
            """),
            {
                'video_id': row['videoId'],
                'title': row['title'],
                'description': row['description'],
                'published_at': row['publishedAt'],
                'likes': row['likes'],
                'views': row['views']
            }
        )

        # Count the number of rows after inserting or updating
        count_after = conn.execute(
            text("SELECT COUNT(*) FROM video")
        ).fetchone()[0]

        # If the number of rows increased, a new record was created
        if count_after > count_before:
            created_videos += 1
        else:
            updated_videos += 1

    conn.commit()
    conn.close()
    return created_videos, updated_videos

# Insert channel data into the SQL database
def insert_channel_data_to_sql(data, channel_name):
    conn = engine.connect()
    reader = csv.DictReader(data.splitlines())
    for row in reader:
        # If the channel data already exists, update the existing record
        conn.execute(
            text("""
                INSERT INTO channel (channel_id, channel_name, subscriber_count, video_count, view_count)
                VALUES (:channel_id, :channel_name, :subscriber_count, :video_count, :view_count)
                ON CONFLICT (channel_id) DO UPDATE SET
                    subscriber_count = EXCLUDED.subscriber_count,
                    video_count = EXCLUDED.video_count,
                    view_count = EXCLUDED.view_count
            """),
            {
                'channel_id': row['channel_id'],
                'channel_name': channel_name,
                'subscriber_count': row['subscriber_count'],
                'video_count': row['video_count'],
                'view_count': row['view_count']
            }
        )
    conn.commit()
    conn.close()

# Insert metadata into ImportTask table
def insert_import_task(start_time, end_time, created_videos, updated_videos, status):
    conn = engine.connect()
    conn.execute(
        text("""
            INSERT INTO import_task (date_start, date_end, created_videos, updated_videos, status)
            VALUES (:date_start, :date_end, :created_videos, :updated_videos, :status)
        """),
        {
            'date_start': start_time,
            'date_end': end_time,
            'created_videos': created_videos,
            'updated_videos': updated_videos,
            'status': status
        }
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
