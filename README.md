# GoodSleep
Local sleep & indoor environment assessment service.

GoodSleep collects indoor environmental parameters, evaluates sleep-friendliness, and provides local analysis suggestions. All data stays on your device.

> Environment shapes sleep.

> An eidolon is not the person. It is the echo left behind.

## ✅ Prerequisites
- Python >= 3.11
- Git
- (Optional) Local LLM runtime: Ollama / llama.cpp

## 📦 Install & Run
```bash
# Clone repo
git clone <your-repo-url>
cd eidolon

# Create virtual environment
python -m venv .venv

# Activate venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (CMD)
.venv\Scripts\activate.bat
# Linux / macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI service
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
