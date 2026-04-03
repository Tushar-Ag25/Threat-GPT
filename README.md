# ThreatGPT 🛡️
**A Secure, Hybrid Edge-Cloud Cybersecurity AI Assistant**

ThreatGPT is a native desktop application designed to provide expert cybersecurity education while actively defending against adversarial prompt engineering. By utilizing a hybrid edge-cloud architecture, it intercepts malicious prompts, jailbreaks, and injection attacks locally on your machine *before* they ever reach the cloud LLM.

## 🚀 Key Features

* **Edge-Based NLP Guardrail:** Powered by a locally hosted, fine-tuned DistilBERT model that classifies user prompts in real-time (<50ms latency). 
* **Stateful "Amnesia" Defense:** A robust Flask backend that utilizes dictionary-based state management. If a malicious prompt is detected, it is retroactively tagged and dropped, ensuring the cloud LLM never ingests or "remembers" adversarial inputs.
* **Native Desktop Experience:** Bypasses traditional browser interfaces using `pywebview` to render a standalone desktop application.
* **Premium UI/UX:** Features a custom "Midnight Lavender" design system with asynchronous JavaScript DOM manipulation for seamless, reload-free text streaming and markdown rendering.
* **Cloud Generative Engine:** Integrates with the OpenRouter API to utilize the powerful `google/gemma-2-9b-it` model for highly technical cybersecurity responses.

## 🧠 System Architecture

ThreatGPT utilizes a Three-Tier Architecture:
1. **Frontend (Client Tier):** HTML5, CSS3, and Vanilla JS wrapped in PyWebView.
2. **Middleware (API & Routing Tier):** Python/Flask server handling state, UUID session generation, and API request routing.
3. **Backend (Inference Tier):** HuggingFace `transformers` (PyTorch) for local guardrail classification + OpenRouter API for generative AI.

## ⚙️ Installation & Setup

### Prerequisites
* Python 3.8+
* Git

### 1. Clone the Repository
```bash
git clone [https://github.com/Tushar-Ag25/Threat-GPT.git](https://github.com/Tushar-Ag25/Threat-GPT.git)
cd Threat-GPT
```
### 2. Create Visual Enviornment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Configure Environment Variables
Create a file named .env in the root directory of the project and add your OpenRouter API key:
```bash
OPENROUTER_API_KEY=your_api_key_here
```
### 5. Add the Local Guardrail Model
(Note: Due to GitHub file size limits, the fine-tuned DistilBERT model weights are not included in this repository.) Ensure your models/ folder contains the necessary pytorch_model.bin and tokenizer.json files before running the application.

### 6. Run the Application
```bash
python app.py

