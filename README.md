# YouTube Data Pipeline

This project consists of two main services that retrieve and process YouTube data, store it in Google Cloud Storage (GCS), and then write it to a PostgreSQL database on Google Cloud SQL. The project is designed to be scheduled using Google Cloud Scheduler and uses Docker Compose for local development.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
  - [Prerequisites](#prerequisites)
  - [Google Cloud Setup](#google-cloud-setup)
  - [Local Development Setup](#local-development-setup)
- [Services](#services)
  - [YouTube Data Retrieval](#youtube-data-retrieval)
  - [Data Processing](#data-processing)
- [Scheduling](#scheduling)
  - [Google Cloud Scheduler](#google-cloud-scheduler)

## Overview

This project is composed of two pipelines:

1. **YouTube Data Retrieval**: Fetches data from YouTube and writes it to Google Cloud Storage.
2. **Data Processing**: Reads data from Google Cloud Storage and writes it to a PostgreSQL database on Google Cloud SQL.

## Setup

### Prerequisites

- Google Cloud account
- Docker and Docker Compose installed
- `gcloud` CLI installed and configured

### Google Cloud Setup

1. **Enable Required APIs:**

    ```bash
    gcloud services enable secretmanager.googleapis.com
    gcloud services enable sqladmin.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable pubsub.googleapis.com
    gcloud services enable cloudscheduler.googleapis.com
    gcloud services enable storage.googleapis.com
    gcloud services enable youtube.googleapis.com
    ```

2. **Set Up Google Cloud SQL:**

    Create a PostgreSQL instance and database on Google Cloud SQL.

3. **Set Up Google Cloud Storage:**

    Create a bucket in Google Cloud Storage.

4. **Set Up Secret Manager:**

    Store the environment variables in Google Cloud Secret Manager:

    ```bash
    gcloud secrets create YOUTUBE_API_KEY --replication-policy="automatic" --data-file=<(echo -n "your_youtube_api_key")
    gcloud secrets create DB_USER --replication-policy="automatic" --data-file=<(echo -n "your_db_user")
    gcloud secrets create DB_PASSWORD --replication-policy="automatic" --data-file=<(echo -n "your_db_password")
    gcloud secrets create DB_NAME --replication-policy="automatic" --data-file=<(echo -n "your_db_name")
    gcloud secrets create GCS_BUCKET_NAME --replication-policy="automatic" --data-file=<(echo -n "your_gcs_bucket_name")
    gcloud secrets create CLOUD_SQL_CONNECTION_NAME --replication-policy="automatic" --data-file=<(echo -n "your_project:your_region:your_instance")
    ```

### Local Development Setup

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/Yromale/IAAS_project.git
    cd youtube-data-pipeline
    ```
2. **Create a environment.env at the root:**
   ```bash
    YOUTUBE_API_KEY=your_youtube_api_key
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_NAME=your_db_name
   ```

3. **Install postgreSQL:**
   Visit the [PostgreSQL](https://www.postgresql.org/download/) download page and choose the appropriate installer for your operating system

4. **Create Database and User:**
    ```bash
    CREATE DATABASE your_database;
    CREATE USER your_db_user WITH PASSWORD your_db_password;
    GRANT ALL PRIVILEGES ON DATABASE your_database TO your_user;
    ```

5. **Build and Run Docker Containers:**

    ```bash
    docker-compose up --build
    ```

## Services

### YouTube Data Retrieval

This service fetches data from YouTube and writes it to Google Cloud Storage.

#### Deployment

1. **Build the Docker Image:**

    ```bash
    docker build -t youtube-data-retrieval:latest -f Dockerfile.youtube_data_retrieval ./retrieval
    ```

2. **Deploy to Cloud Run:**

    ```bash
    gcloud run deploy youtube-data-retrieval --image gcr.io/your_project/youtube-data-retrieval:latest --region your_region --platform managed --allow-unauthenticated
    ```

### Data Processing

This service reads data from Google Cloud Storage and writes it to a PostgreSQL database on Google Cloud SQL.

#### Deployment

1. **Build the Docker Image:**

    ```bash
    docker build -t data-processing:latest -f Dockerfile.data_processing ./process
    ```

2. **Deploy to Cloud Run:**

    ```bash
    gcloud run deploy data-processing --image gcr.io/your_project/data-processing:latest --region your_region --platform managed --allow-unauthenticated
    ```

## Scheduling

### Google Cloud Scheduler

1. **Create Pub/Sub Topics:**

    ```bash
    gcloud pubsub topics create youtube-data-retrieval-topic
    gcloud pubsub topics create data-processing-topic
    ```

2. **Create Scheduler Jobs:**

    ```bash
    gcloud scheduler jobs create pubsub youtube-data-retrieval-job --schedule="0 18 * * *" --time-zone="UTC" --topic=youtube-data-retrieval-topic --message-body="Trigger YouTube Data Retrieval"
    gcloud scheduler jobs create pubsub data-processing-job --schedule="30 18 * * *" --time-zone="UTC" --topic=data-processing-topic --message-body="Trigger Data Processing"
    ```

## Destroying a Job

To delete a Cloud Scheduler job:

```bash
gcloud scheduler jobs delete youtube-data-retrieval-job
gcloud scheduler jobs delete data-processing-job
```


This `README.md` covers the essential steps and configurations needed to set up and deploy the YouTube data pipeline using Google Cloud services and Docker Compose for local development. It includes instructions for setting up environment variables, enabling required APIs, deploying services, and scheduling jobs with Google Cloud Scheduler and Celery.

