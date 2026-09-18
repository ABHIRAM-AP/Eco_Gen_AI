import google.generativeai as genai
import os,requests
from src.ingestion_layer.collectors.gen_ai_data import track_inference

MODEL_NAME="gemini-3.5-flash"


# genai.configure(api_key="")
# model=genai.GenerativeModel(MODEL_NAME)

# @track_inference(model_name=MODEL_NAME,task_type="text-gen",provider="gemini")
# def call_gemini(prompt):
#     return model.generate_content(prompt)

# resp=call_gemini("Explain Quantum Computing in 5 sentences?")
# print(resp.usage_metadata)
# print(call_gemini.last_event)



@track_inference(model_name="gemma3:270m", task_type="text-gen", provider="ollama")
def call_ollama(prompt):
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "gemma3:270m", "prompt": prompt, "stream": False},
        timeout=60
    )
    return resp.json()

# in your test_ollama.py — wrap with a print to see the raw response
result = call_ollama("Explain Quantum Computing in 5 sentences")
print("RAW RESPONSE:", result)   # add this — will show an error message if the call failed
print(result.get("response"))
print(call_ollama.last_event)


