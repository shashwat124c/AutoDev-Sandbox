from flask import Flask, request, jsonify
from celery.result import AsyncResult
from tasks import async_developer_task
from celery_app import app as celery_instance

# Initialize the Flask web server application instance
app = Flask(__name__)

# =====================================================================
# ENDPOINT 1: DISPATCH TASK (POST /api/dev-task)
# =====================================================================
@app.route('/api/dev-task', methods=['POST'])
def trigger_developer_task():
    """
    Accepts a user prompt over HTTP, hands it to the Redis queue instantly,
    and returns a non-blocking tracking Task ID back to the client.
    """
    data = request.get_json() or {}
    user_prompt = data.get('prompt')
    
    if not user_prompt:
        return jsonify({"error": "Missing required field: 'prompt'"}), 400
        
    print(f"🌐 HTTP Request Received. Dispatching prompt to Redis pipeline...")
    
    # Send the task to our Celery worker pool asynchronously
    task = async_developer_task.delay(user_prompt)
    
    # Respond immediately to keep the HTTP connection brief and prevent timeouts
    return jsonify({
        "status": "queued",
        "task_id": task.id,
        "message": "Agent loop successfully dispatched to background workers."
    }), 202


# =====================================================================
# ENDPOINT 2: MONITOR STATUS (GET /api/dev-task/status/<task_id>)
# =====================================================================
@app.route('/api/dev-task/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Looks up the live progress state of a background worker task directly
    from the Redis backend storage cell using its unique Task ID.
    """
    # Bind to the active tracking result cell inside Redis
    result = AsyncResult(task_id, app=celery_instance)
    
    response_payload = {
        "task_id": task_id,
        "state": result.state # Can return: PENDING, STARTED, SUCCESS, or FAILURE
    }
    
    # If the background worker has finished running the self-correction engine loop
    if result.ready():
        if result.successful():
            # If the task completed cleanly, append the final engine dictionary payload
            response_payload["result"] = result.result
        else:
            # If the task threw an unhandled runtime error
            response_payload["error"] = str(result.info)
            
    return jsonify(response_payload), 200

if __name__ == '__main__':
    # Start the local development web server on port 5000
    app.run(debug=True, port=5000)