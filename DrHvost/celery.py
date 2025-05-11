# myproject/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DrHvost.settings')  # замени myproject на имя проекта

app = Celery('DrHvost')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
