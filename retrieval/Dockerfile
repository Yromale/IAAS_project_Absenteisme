FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Install the Cloud SQL Proxy
RUN apt-get update && apt-get install -y wget \
    && wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy \
    && chmod +x cloud_sql_proxy

COPY . .

# Start the Cloud SQL Proxy and your application
CMD ./cloud_sql_proxy -dir=/cloudsql & python youtube_data_retrieval.py
