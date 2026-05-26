import os
import time
from pydantic import BaseModel, Field
import google.generativeai as genai
from sandbox import ExecutionSandbox

class CoderResponseSchema(BaseModel):
    explanation: str = Field(description="Brief planning thoughts or a description of what the script does.")
    filename: str = Field(description="The name of the file to create (e.g., 'scraper.py').")
    code: str = Field(description="The complete, production-ready Python source code text.")
    run_command: str = Field(description="The exact terminal execution command (e.g., 'python scraper.py').")

def run_autonomous_developer(user_prompt: str, max_retries: int = 4) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ Missing Environment Variable: Please set GEMINI_API_KEY")
        
    genai.configure(api_key=api_key)
    
    system_instruction = (
        "You are an expert autonomous software engineer executing operations in an isolated Linux container. "
        "Your goal is to build high-quality, completely functional scripts that fulfill the user's request."
    )
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_instruction
    )
    
    workspace_id = f"dev_task_{int(time.time())}"
    print(f"📦 Workspace initialized: {workspace_id}")
    sandbox = ExecutionSandbox(workspace_id=workspace_id, timeout_seconds=10)
    
    history_context = f"User Request: {user_prompt}"
    attempt = 0
    
    try:
        while attempt < max_retries:
            attempt += 1
            print(f"\n==================================================")
            print(f"🤖 [LOOP ATTEMPT {attempt}/{max_retries}] Calling Agent Engine...")
            print(f"==================================================")
            
            response = model.generate_content(
                history_context,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=CoderResponseSchema,
                    temperature=0.3
                )
            )
            
            agent_data = CoderResponseSchema.model_validate_json(response.text)
            
            # ─────────────────────────────────────────────────────────
            # INTERMEDIARY STEP 1: INSPECTING GENERATED CODE
            # ─────────────────────────────────────────────────────────
            print(f"\n[INTERMEDIARY LOG] Agent Rationale: {agent_data.explanation}")
            print(f"[INTERMEDIARY LOG] Target Filename: {agent_data.filename}")
            print(f"\n--- 📄 RAW GENERATED CODE CODE (Attempt {attempt}) ---")
            print(agent_data.code.strip())
            print(f"──────────────────────────────────────────────────\n")
            
            sandbox.write_file(agent_data.filename, agent_data.code)
            
            print(f"[INTERMEDIARY LOG] Spawning container with command: `{agent_data.run_command}`")
            execution = sandbox.execute_command(agent_data.run_command)
            
            # ─────────────────────────────────────────────────────────
            # INTERMEDIARY STEP 2: INSPECTING CONTAINER TELEMETRY
            # ─────────────────────────────────────────────────────────
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
            
            # ─────────────────────────────────────────────────────────
            # INTERMEDIARY STEP 3: CONTEXT STREAM RE-INJECTION
            # ─────────────────────────────────────────────────────────
            print(f"\n--- 🔄 RE-INJECTING FEEDBACK INTO LLM CONTEXT ---")
            print(f"Appending error logs to history state for next iteration calculation.")
            print(f"──────────────────────────────────────────────────\n")
            
            history_context += feedback_payload
            
        return {
            "status": "failed",
            "attempts_required": max_retries,
            "error": "Could not patch code to execute cleanly within retry boundaries."
        }
        
    finally:
        print("🧹 Tearing down active runtime sandbox environment...")
        sandbox.cleanup()