import os
from agent_engine import run_autonomous_developer # If running in the same directory, use: from agent_engine import run_autonomous_developer

def main():
    # SET YOUR API KEY FOR THE RUNTIME SESSION
    # Replace this string with your real Gemini API key from AI Studio
    os.environ["GEMINI_API_KEY"] = "AIzaSyCCU5x12EdYlsoZ0OH2Qph3MVXn35jZFhs"
    
    # Challenge prompt: An intentionally tricky task where a model might easily make an initial typo
    prompt = (
    "Write a Python script that fetches the current price of Bitcoin from the Coingecko API "
    "(https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd) "
    "using the requests library. Print the price cleanly to the console. "
    "Note: The container environment has no third-party libraries pre-installed, "
    "but you have full freedom to install what you need via your execution command."
)
    
    print("🔥 Starting AegisCompute Self-Correction Test Engine 🔥")
    result = run_autonomous_developer(prompt)
    
    print("\n================ FINAL REPORT ================")
    print(f"Status: {result['status'].upper()}")
    print(f"Total Self-Correction Loops: {result['attempts_required']}")
    
    if result['status'] == 'success':
        print(f"Verified Filename: {result['filename']}")
        print("\n--- Verified Script Execution Output ---")
        print(result['output'])
    else:
        print(f"Failure Reason: {result['error']}")
    print("==============================================")

if __name__ == "__main__":
    main()