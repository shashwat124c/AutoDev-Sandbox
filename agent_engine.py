import os
import time
from pydantic import BaseModel, Field
import google.genai as genai  # <-- Updated modern import
from google.genai import types  # <-- Needed for config structures
from sandbox import ExecutionSandbox

class CoderResponseSchema(BaseModel):
    explanation: str = Field(description="Brief planning thoughts or a description of what the script does.")
    filename: str = Field(description="The name of the file to create (e.g., 'scraper.py').")
    code: str = Field(description="The complete, production-ready Python source code text.")
    run_command: str = Field(description="The exact terminal execution command (e.g., 'python scraper.py').")
    expected_output_marker: str = Field(description="A distinct text phrase or structural marker that MUST appear in the stdout log if the code ran successfully (e.g., 'Current Bitcoin Price:')")

def run_autonomous_developer(user_prompt: str, max_retries: int = 4) -> dict:
    # 1. Initialize the modern GenAI Client
    # The new SDK automatically looks for the GEMINI_API_KEY env variable natively
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("❌ Missing Environment Variable: Please set GEMINI_API_KEY in your .env file")
        
    client = genai.Client()  # <-- Created stateless modern client instantiation
    
    workspace_id = f"dev_task_{int(time.time())}"
    print(f"📦 Workspace initialized: {workspace_id}")
    sandbox = ExecutionSandbox(workspace_id=workspace_id, timeout_seconds=10)
    
    history_context = f"User Request: {user_prompt}"
    attempt = 0
    
    try:
        while attempt < max_retries:
            attempt += 1
            print(f"\n==================================================")
            print(f"🤖 [LOOP ATTEMPT {attempt}/{max_retries}] Calling Modern Agent Engine...")
            print(f"==================================================")
            
            # The modern client uses client.models.generate_content
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=history_context,
                config=types.GenerateContentConfig(  # <-- Updated modern config contract
                    response_mime_type="application/json",
                    response_schema=CoderResponseSchema,
                    temperature=0.3,
                    system_instruction="You are an expert autonomous software engineer executing operations in an isolated Linux container."
                )
            )
            
            # The new SDK automatically parses the JSON directly into your Pydantic object
            # accessible via the response.parsed attribute!
            agent_data = response.parsed
            
            print(f"\n[INTERMEDIARY LOG] Agent Rationale: {agent_data.explanation}")
            print(f"[INTERMEDIARY LOG] Target Filename: {agent_data.filename}")
            print(f"\n--- 📄 RAW GENERATED CODE (Attempt {attempt}) ---")
            print(agent_data.code.strip())
            print(f"──────────────────────────────────────────────────\n")
            
            sandbox.write_file(agent_data.filename, agent_data.code)
            
            print(f"[INTERMEDIARY LOG] Spawning container with command: `{agent_data.run_command}`")
            execution = sandbox.execute_command(agent_data.run_command)
            
            print(f"\n--- 🖥️ DOCKER TERMINAL OUTPUT (Attempt {attempt}) ---")
            print(f"Exit Code Received: {execution['exit_code']}")
            print("Console Output:")
            print(execution['output'] if execution['output'] else "[Console was empty]")
            print(f"──────────────────────────────────────────────────\n")
            
            if execution["exit_code"] == 0:
                print(f"🎯 State Reached: SUCCESS on Attempt {attempt}!")
                return {
                    "status": "success",
                    "attempts_required": attempt,
                    "filename": agent_data.filename,
                    "code": agent_data.code,
                    "output": execution["output"]
                }
            
            print(f"⚠️ State Reached: CRASH DETECTED. Building feedback payload...")
            
            feedback_payload = (
                f"\n\n[System Feedback - Attempt {attempt} Failed]\n"
                f"The file '{agent_data.filename}' you wrote crashed with exit code {execution['exit_code']}.\n"
                f"Here are the absolute terminal logs / error traces:\n{execution['output']}\n"
                f"Analyze the mistake, rewrite the complete script, and provide corrected variables."
            )
            
            history_context += feedback_payload
            
        return {
            "status": "failed",
            "attempts_required": max_retries,
            "error": "Could not patch code to execute cleanly within retry boundaries."
        }
        
    finally:
        print("🧹 Tearing down active runtime sandbox environment...")
        sandbox.cleanup()