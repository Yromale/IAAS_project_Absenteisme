import os
import requests
import csv
from google.cloud import storage, secretmanager
from flask import Flask
from dotenv import load_dotenv



app = Flask(__name__)

# Load environment variables from .env file
load_dotenv("environment.env")

def access_secret_version(secret_id):
    project_id = os.getenv('PROJECT_ID')
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = secret_client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode('UTF-8')


# Check if environment.env file is present
if os.path.exists("environment.env"):
    # Load environment variables from .env file
    load_dotenv("environment.env")
    API_KEY = os.getenv('YOUTUBE_API_KEY')
    BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
else:
    # Secret Manager client
    secret_client = secretmanager.SecretManagerServiceClient()

    # Retrieve secrets
    API_KEY = access_secret_version('YOUTUBE_API_KEY')
    BUCKET_NAME = access_secret_version('GCS_BUCKET_NAME')


@app.route('/')
def main():
    channels = {
        'UCfpCQ89W9wjkHc8J_6eTbBg': 'OutdoorBoys',
        'UCHNPI6vNmspHR49e7EnWc_g': 'pacificsound3003',
        'UCJLZe_NoiG0hT7QCX_9vmqw': 'Ididathing'
    }

    channel_data = []
    for channel_id, channel_name in channels.items():
        channel_data.append(get_channel_data(channel_id))

        video_data = get_youtube_data(channel_id)

        # Create Data folder if it doesn't exist
        if not os.path.exists('Data'):
            os.makedirs('Data')
        filename = f"Data/{channel_name}_data.csv"
        
        with open(filename, 'w', newline='',encoding='utf-8-sig') as csvfile:
            fieldnames = ['videoId', 'title', 'description', 'publishedAt', 'likes', 'views', 'comments']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in video_data:
                if item['id']['kind'] == 'youtube#video':  # Ensure the item is a video
                    video_id = item['id']['videoId']
                    likes, views, comments = get_video_stats(video_id)
                    writer.writerow({
                        'videoId': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'publishedAt': item['snippet']['publishedAt'],
                        'likes': likes,
                        'views': views,
                        'comments': comments
                    })
        
        # Upload file to Google Cloud Storage if running on GCP
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            with open(filename, 'r') as file:
                upload_to_gcs(filename, file.read())
    
    save_channel_data(channel_data)

    return "Data retrieval complete"

# Function to retrieve data from YouTube API
def get_youtube_data(channel_id):
    url = f"https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=50"
    data = []
    while url:
        response = requests.get(url)
        result = response.json()
        if 'error' in result:
            # Handle API error, e.g., log the error message or raise an exception
            error_message = result['error']['message']
            raise Exception(f'YouTube API error: key={API_KEY} channelId={channel_id}0')
        data.extend(result['items'])
        url = result.get('nextPageToken', None)
        if url:
            url = f"https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=50&pageToken={result['nextPageToken']}"
        break  # Remove this line to retrieve all videos
    return data

# Function to retrieve video statistics
def get_video_stats(video_id):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={API_KEY}"
    response = requests.get(url)
    result = response.json()
    if 'items' in result and result['items']:
        stats = result['items'][0]['statistics']
        return stats.get('likeCount', '0'), stats.get('viewCount', '0'), stats.get('commentCount', '0')
    return '0', '0', '0'

# Function to retrieve channel data
def get_channel_data(channel_id):
    url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={API_KEY}"
    response = requests.get(url)
    result = response.json()
    if 'items' in result and result['items']:
        item = result['items'][0]
        return {
            'channel_id': channel_id,
            'channel_name': item['snippet'].get('title', ''),
            'description': item['snippet'].get('description', ''),
            'subscriber_count': item['statistics'].get('subscriberCount', '0'),
            'video_count': item['statistics'].get('videoCount', '0'),
            'view_count': item['statistics'].get('viewCount', '0')
        }
    return {}

# Function to save channel data to CSV file
def save_channel_data(channel_data):
    for i in channel_data:
        filename = f"Data/{i['channel_name']}_channel_data.csv"
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['channel_id', 'channel_name', 'description', 'subscriber_count', 'video_count', 'view_count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                'channel_id': i['channel_id'],
                'channel_name': i['channel_name'],
                'description': i['description'],
                'subscriber_count': i['subscriber_count'],
                'video_count': i['video_count'],
                'view_count': i['view_count']
            })
        # Upload file to Google Cloud Storage if running on GCP
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            with open(filename, 'r') as file:
                upload_to_gcs(filename, file.read())
            
# Function to upload file to Google Cloud Storage
def upload_to_gcs(filename, data):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(data, content_type='text/csv')


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
