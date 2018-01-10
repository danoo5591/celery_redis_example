from __future__ import absolute_import
import os
from django.conf import settings
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celery_try.settings')
app = Celery('celery_try',
             backend='redis',
             broker='redis://localhost:6379/0')

# This reads, e.g., CELERY_ACCEPT_CONTENT = ['json'] from settings.py:
app.config_from_object('django.conf:settings')

# For autodiscover_tasks to work, you must define your tasks in a file called 'tasks.py'.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# app.conf.CELERY_QUEUES = (
#     Queue('testapp.queue'),
# )

# The following lines may contains pseudo-code
from celery.schedules import crontab
# Other Celery settings
app.conf.CELERYBEAT_SCHEDULE = {
    'sum_task': {
        'task': 'testapp.tasks.sum_task',
        'schedule': crontab(hour=7, minute=30, day_of_week=1), # Every second
    },
    'random_sum': {
        'task': 'testapp.tasks.random_sum',
        'schedule': 5, # Every second
    },
}

# @app.task(queue='testapp.queue')
# def another_task(self):
#     print("another_task")

@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))