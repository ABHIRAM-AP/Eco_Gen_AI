import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from src.ingestion_layer.collectors.gen_ai_data import track_inference

# Load environment variables (.env)
load_dotenv()

# ===========================================================================
# 1. Google Gemini Cloud API Setup
# ===========================================================================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = "gemini-3.5-flash"

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY, transport="rest")
    gemini_client = genai.GenerativeModel(GEMINI_MODEL_NAME)

    @track_inference(
        model_name=GEMINI_MODEL_NAME,
        task_type="text-gen",
        provider="gemini",
        department="Product",
        region="US-CAL-CISO"
    )
    def call_gemini(prompt: str):
        """Executes a tracked inference query via Google Gemini API."""
        return gemini_client.generate_content(prompt)


# ===========================================================================
# 2. Local Ollama Setup
# ===========================================================================
OLLAMA_MODEL_NAME = "gemma3:270m"

@track_inference(
    model_name=OLLAMA_MODEL_NAME,
    task_type="text-gen",
    provider="ollama",
    department="Engineering",
    region="US-CAL-CISO"
)
def call_ollama(prompt: str):
    """Executes a tracked inference query via local Ollama daemon."""
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": OLLAMA_MODEL_NAME, "prompt": prompt, "stream": False},
        timeout=60
    )
    return resp.json()


# ===========================================================================
# Execution / Test Runner
# ===========================================================================
if __name__ == "__main__":
    prompt = "Explain Quantum Computing in 2 sentences"

    # --- Test Gemini ---
    if GEMINI_KEY:
        print("\n=== Testing Google Gemini API ===")
        gemini_resp = call_gemini(prompt)
        print("Gemini Output:", gemini_resp.text.strip())
        print("Logged Event:", call_gemini.last_event)

    # --- Test Ollama (uncomment if ollama serve is active) ---
    # print("\n=== Testing Local Ollama ===")
    # ollama_resp = call_ollama(prompt)
    # print("Ollama Output:", ollama_resp.get("response"))
    # print("Logged Event:", call_ollama.last_event)
