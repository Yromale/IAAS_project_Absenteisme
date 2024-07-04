from celery import Celery
import subprocess

app = Celery('tasks')
app.config_from_object('celeryconfig')

@app.task
def data_processing():
    subprocess.run(["python", "./process/data_processing.py"])

@app.task
def youtube_data_retrieval():
    subprocess.run(["python", "./retrieval/youtube_data_retrieval.py"])
