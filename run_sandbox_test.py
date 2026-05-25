from sandbox import ExecutionSandbox
import time

def run_test():
    print("🚀 Initializing Test Sandbox...")
    # Create a unique sandbox workspace ID
    box = ExecutionSandbox(workspace_id=f"test_run_{int(time.time())}")
    
    # 1. Simulate the AI writing a python script
    broken_code = (
        "import sys\n"
        "print('Step 1: Running basic calculations...')\n"
        "result = 10 / 5\n" # This will intentionally crash with ZeroDivisionError
        "print(f'Step 2: Done! Result is {result}')"
    )
    
    print("📝 Writing simulated script to workspace...")
    box.write_file("calculator.py", broken_code)
    
    # 2. Run the code inside our isolated container
    print("🏃 Executing code inside the sandbox container...")
    result = box.execute_command("python calculator.py")
    
    # 3. Print the results trapped by the backend wrapper
    print("\n--- Sandbox Results ---")
    print(f"Exit Code: {result['exit_code']} (Anything other than 0 is an error)")
    print("Terminal Logs:")
    print(result['output'])
    print("------------------------\n")
    
    # 4. Clean up the host files
    print("🧹 Cleaning up host workspace directory...")
    box.cleanup()
    print("✨ Phase 1 Testing Complete!")

if __name__ == "__main__":
    run_test()