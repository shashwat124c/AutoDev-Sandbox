from celery_app import app
from agent_engine import run_autonomous_developer
from dotenv import load_dotenv

# Ensure environment variables (.env) load properly inside the separate worker thread
load_dotenv()

@app.task(bind=True)
def async_developer_task(self, user_prompt: str):
    """
    Wraps our self-correcting agent loop into an async task container.
    """
    print(f"🚀 Celery Background Worker accepted Task ID: {self.request.id}")
    
    # Run the modern, internet-enabled agent loop
    result = run_autonomous_developer(user_prompt)
    
    # Celery automatically saves this return dict to Redis under the unique Task ID
    return result