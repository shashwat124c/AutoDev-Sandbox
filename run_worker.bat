@echo off
call myenv\Scripts\activate
echo 🧠 Starting AegisCompute Async Celery Worker Stack...
celery -A tasks worker --loglevel=info -P solo
pause