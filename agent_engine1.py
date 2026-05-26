import os
import time
from pydantic import BaseModel, Field
import google.generativeai as genai
from sandbox import ExecutionSandbox

# =====================================================================
# PHASE 2: THE STRUCTURED DATA CONTRACT
# =====================================================================
class CoderResponseSchema(BaseModel):
    """
    The blueprint that Gemini MUST follow. It forces the LLM to return
    clean, machine-readable data instead of unstructured conversational text.
    """
    explanation: str = Field(description="Brief planning thoughts or a description of what the script does.")
    filename: str = Field(description="The name of the file to create (e.g., 'scraper.py').")
    code: str = Field(description="The complete, production-ready Python source code text.")
    run_command: str = Field(description="The exact terminal execution command (e.g., 'python scraper.py').")


# =====================================================================
# PHASE 3: THE AUTONOMOUS AGENT ORCHESTRATOR
# =====================================================================
def run_autonomous_developer(user_prompt: str, max_retries: int = 4) -> dict:
    """
    Takes a user prompt, asks Gemini to write code, executes it inside 
    the secure Docker sandbox, and iterates automatically if errors are caught.
    """
    # 1. Initialize the Gemini API client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ Missing Environment Variable: Please set GEMINI_API_KEY")
        
    genai.configure(api_key=api_key)
    
    system_instruction = (
        "You are an expert autonomous software engineer executing operations in an isolated Linux container. "
        "Your goal is to build high-quality, completely functional scripts that fulfill the user's request. "
        "Always write clean code and ensure you do not use conversational markdown formatting outside the requested schema."
    )
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_instruction
    )
    
    # 2. Spin up a fresh, unique Execution Sandbox workspace
    workspace_id = f"dev_task_{int(time.time())}"
    print(f"📦 Creating secure workspace: {workspace_id}")
    sandbox = ExecutionSandbox(workspace_id=workspace_id, timeout_seconds=10)
    
    # Initialize our conversational memory stream
    history_context = f"User Request: {user_prompt}"
    attempt = 0
    
    try:
        while attempt < max_retries:
            attempt += 1
            print(f"\n🤖 [Attempt {attempt}/{max_retries}] Invoking Gemini Coder Agent...")
            
            # Request structured code delivery from Gemini
            response = model.generate_content(
                history_context,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=CoderResponseSchema,
                    temperature=0.2 # Lower temperature forces precise, deterministic logic
                )
            )
            
            # Parse the validated data structure
            agent_data = CoderResponseSchema.model_validate_json(response.text)
            
            print(f"📝 Agent plans to create: '{agent_data.filename}'")
            print(f"💡 Agent rationale: {agent_data.explanation}")
            
            # Write the generated code string directly into our sandbox volume
            sandbox.write_file(agent_data.filename, agent_data.code)
            
            print(f"🏃 Executing command inside Docker: `{agent_data.run_command}`")
            execution = sandbox.execute_command(agent_data.run_command)
            
            print(f"📊 Container finished with Exit Code: {execution['exit_code']}")
            
            # -----------------------------------------------------------------
            # THE CORE CONDITION CHECK: CRASH MONITOR
            # -----------------------------------------------------------------
            if execution["exit_code"] == 0:
                print("🎉 SUCCESS! The script compiled and executed perfectly on the first try.")
                return {
                    "status": "success",
                    "attempts_required": attempt,
                    "filename": agent_data.filename,
                    "code": agent_data.code,
                    "output": execution["output"]
                }
            
            # If we reached this line, the exit code was NOT 0 (Code Crashed!)
            print("⚠️ Code crashed or timed out. Capturing runtime diagnostics for feedback...")
            print(f"❌ Error Traceback trapped:\n{execution['output']}")
            
            # Feed the exact console error back into the AI context history loop
            history_context += (
                f"\n\n[System Feedback - Attempt {attempt} Failed]\n"
                f"The file '{agent_data.filename}' you wrote crashed with exit code {execution['exit_code']}.\n"
                f"Here are the absolute terminal logs / error traces:\n{execution['output']}\n"
                f"Analyze the mistake, rewrite the complete script, and provide corrected variables."
            )
            
        # If the loop exhausts all retries without an exit code of 0
        return {
            "status": "failed",
            "attempts_required": max_retries,
            "error": "Could not patch code to execute cleanly within retry boundaries."
        }
        
    finally:
        # Guarantee cleanup happens to avoid hard drive pollution
        print("🧹 Tearing down active runtime sandbox environment...")
        sandbox.cleanup()