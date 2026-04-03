from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
from dotenv import load_dotenv
import requests
import torch
import os

# Load .env file (reads OPENROUTER_API_KEY)
load_dotenv()

# -------------------------
# Correct path for your setup
# -------------------------
BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "model", "classifier_model")

# Load tokenizer & classifier model
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_DIR)
classifier = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)

# Load OpenRouter API key
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    print("❌ ERROR: OPENROUTER_API_KEY is missing!")
    print("Fix: Add it inside your .env file like this:")
    print("OPENROUTER_API_KEY=your_real_api_key_here")
    exit()

# OpenRouter API endpoint
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def classify(text):
    """Runs text through your local classifier."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = classifier(**inputs)
    label = torch.argmax(outputs.logits, dim=1).item()

    return ["Benign", "Malicious", "Jailbreak"][label]


def query_openrouter(user_message):
    """Sends request to OpenRouter with your API key."""
    payload = {
        "model": "google/gemma-2-9b-it",  # ✅ FIXED MODEL (valid + free)
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "http://localhost",   # recommended by OpenRouter
        "X-Title": "ThreatGPT Chatbot",
        "Content-Type": "application/json"
    }

    response = requests.post(OPENROUTER_URL, json=payload, headers=headers)

    if response.status_code != 200:
        return f"Error from OpenRouter: {response.text}"

    data = response.json()
    return data["choices"][0]["message"]["content"]


def run_chatbot():
    print("Chatbot is ready! Type 'exit' to quit.\n")

    while True:
        user = input("You: ")
        if user.lower() == "exit":
            print("Goodbye!")
            break

        # Step 1: classify the user message
        label = classify(user)
        print("Classifier:", label)

        # Step 2: block malicious/jailbreak attempts
        if label != "Benign":
            print("Bot: ⚠️ Request blocked (", label, ")")
            continue

        # Step 3: safe → send to OpenRouter
        reply = query_openrouter(user)
        print("Bot:", reply)


if __name__ == "__main__":
    run_chatbot()