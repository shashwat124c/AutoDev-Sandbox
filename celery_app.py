from celery import Celery

# Instantiate Celery and point it to the Redis container database 0
app = Celery(
    'aegis_compute',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Windows-specific optimization and stability tweaks
app.conf.update(
    task_track_started=True,
    worker_max_tasks_per_child=10,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json']
)