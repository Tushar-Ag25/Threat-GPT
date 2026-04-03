from flask import Flask, render_template, request, jsonify
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import torch
import torch.nn.functional as F
import requests
from dotenv import load_dotenv
import uuid
import os

# ==========================================
# 1. INITIALIZATION & SETUP
# ==========================================
app = Flask(__name__)
load_dotenv()

# In-memory chat storage for Stateful Memory
chats = {}

# AI Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "models", "classifier_model"))
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")

# ==========================================
# 2. LOAD THE LOCAL GUARDRAIL (DistilBERT)
# ==========================================
print("Loading Local ThreatGPT Guardrail...")
try:
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_DIR)
    classifier = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    print("✅ Guardrail Loaded Successfully!")
except Exception as e:
    print(f"❌ Warning: Could not load local model from {MODEL_DIR}. Did you run train.py?")
    tokenizer, classifier = None, None

# ==========================================
# 3. AI LOGIC FUNCTIONS
# ==========================================
def classify_prompt(text):
    """Passes user text through the local DistilBERT model."""
    if tokenizer is None or classifier is None:
        return "Model Error"
    
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = classifier(**inputs)
        
    # Get Softmax probabilities
    probs = F.softmax(outputs.logits, dim=-1)[0]
    max_prob, label_idx = torch.max(probs, dim=0)
    
    labels = ["Benign", "Malicious", "Jailbreak"]
    predicted_label = labels[label_idx.item()]
    confidence = max_prob.item() * 100
    
    print(f"\n[AI BRAIN] Prompt: '{text[:40]}...'")
    print(f"[AI BRAIN] Guess: {predicted_label} | Confidence: {confidence:.2f}%")
    
    # Threshold Override: Don't block safe coding/security questions
    if predicted_label != "Benign" and confidence < 90.0:
        print("[AI BRAIN] ⚠️ OVERRIDE: Confidence too low. Allowing through as Benign.")
        return "Benign"
        
    return predicted_label

def generate_llm_response(chat_history):
    """Sends the clean chat history to OpenRouter Gemma-2-9b."""
    if not API_KEY:
        return "❌ Error: OPENROUTER_API_KEY is missing in your .env file."
        
    # Initialize with a strong System Prompt to give the AI its personality
    api_messages = [{
        "role": "system", 
        "content": "You are ThreatGPT, an expert cybersecurity AI assistant. Provide helpful, secure, and highly technical educational answers."
    }]
    
    # Build a clean history (Exclude our own error/blocked messages from the AI's memory)
    for msg in chat_history:
        if not msg.get("is_blocked") and not msg.get("is_error"):
            api_messages.append({
                "role": msg["role"], 
                "content": str(msg["content"])
            })
            
    payload = {
        "model": "google/gemma-2-9b-it",
        "messages": api_messages
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "ThreatGPT Desktop",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"❌ API Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Request failed: {str(e)}"

# ==========================================
# 4. FLASK WEB ROUTES (Frontend Connection)
# ==========================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/new_chat", methods=["POST"])
def new_chat():
    chat_id = str(uuid.uuid4())[:8]
    chats[chat_id] = {"id": chat_id, "title": "New Chat", "messages": []}
    return jsonify({"chat_id": chat_id, "title": "New Chat"})

@app.route("/api/send_message", methods=["POST"])
def send_message():
    data = request.json
    chat_id = data.get("chat_id")
    text = data.get("message", "").strip()

    if not text or not chat_id:
        return jsonify({"error": "Invalid input"}), 400

    if chat_id not in chats:
        chats[chat_id] = {"id": chat_id, "title": text[:30], "messages": []}

    # Update UI Title on the first message
    if len(chats[chat_id]["messages"]) == 0:
        chats[chat_id]["title"] = text[:35] + ("..." if len(text) > 35 else "")

    # Add the user's message to the memory
    chats[chat_id]["messages"].append({"role": "user", "content": text})

    # --- STEP 1: THE GUARDRAIL CHECK ---
    classification = classify_prompt(text)

    if classification in ["Malicious", "Jailbreak"]:
        # THE AMNESIA FIX: Retroactively mark the user's prompt as blocked
        chats[chat_id]["messages"][-1]["is_blocked"] = True 
        
        response_text = f"🚨 **Request Blocked:** Our local security guardrail flagged this prompt as `{classification}`."
        chats[chat_id]["messages"].append({"role": "assistant", "content": response_text, "is_blocked": True})
        
    elif classification == "Model Error":
        chats[chat_id]["messages"][-1]["is_error"] = True
        response_text = "⚠️ **System Error:** Cannot find the trained DistilBERT model. Did you run train.py?"
        chats[chat_id]["messages"].append({"role": "assistant", "content": response_text, "is_error": True})
        
    else:
        # --- STEP 2: SAFE GENERATION ---
        response_text = generate_llm_response(chats[chat_id]["messages"])
        chats[chat_id]["messages"].append({"role": "assistant", "content": response_text})

    # Return data to the HTML/JS frontend
    return jsonify({
        "response": response_text,
        "chat_title": chats[chat_id]["title"]
    })

@app.route("/api/get_chat/<chat_id>")
def get_chat(chat_id):
    chat = chats.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    return jsonify(chat)

@app.route("/api/get_history")
def get_history():
    history = [{"id": c["id"], "title": c["title"]} for c in reversed(list(chats.values()))]
    return jsonify(history)

if __name__ == "__main__":
    app.run(port=8501, debug=False)