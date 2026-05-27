import time
from dotenv import load_dotenv
from tasks import async_developer_task
from celery.result import AsyncResult

load_dotenv()

def main():
    prompt = (
        "Write a Python script that fetches the current price of Bitcoin from the Coingecko API "
        "(https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd) "
        "using the requests library. Print the price cleanly to the console."
    )
    
    print("🔥 Sending task to the asynchronous Redis broker queue...")
    
    # .delay() pushes the job into Redis and returns a non-blocking tracking token immediately
    task = async_developer_task.delay(prompt)
    
    print(f"🎯 Task successfully queued! Generated Task ID: {task.id}")
    print("⏳ Polling task execution state from the background worker...")
    
    # Poll the status of the task until it completes
    while not task.ready():
        print(f"Current Worker State: {task.state}...")
        time.sleep(3)
        
    # Grab the final evaluation payload out of the Redis backend storage cell
    final_result = task.result
    
    print("\n================ ASYNC EXECUTION COMPLETE ================")
    print(f"Final Status: {final_result['status'].upper()}")
    print(f"Attempts Needed: {final_result['attempts_required']}")
    print(f"Filename Created: {final_result['filename']}")
    print("\n--- Verified Script Output Captured from Worker ---")
    print(final_result['output'].strip())
    print("==========================================================")

if __name__ == "__main__":
    main()