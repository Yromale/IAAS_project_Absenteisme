from celery import Celery
from celery.schedules import crontab

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

app.conf.beat_schedule = {
    'run-data-processing': {
        'task': 'process.data_processing.run_data_processing',
        'schedule': crontab(hour=18, minute=0),  # 6:00 PM
    },
    'run-youtube-data-retrieval': {
        'task': 'retrieval.youtube_data_retrieval.run_youtube_data_retrieval',
        'schedule': crontab(hour=18, minute=30),  # 6:30 PM
    },
}

app.conf.timezone = 'UTC'
