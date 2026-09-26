# 🎙️ AI Interviewer Platform

An intelligent, real-time adaptive technical interview platform featuring **Voice Narration (Deepgram TTS)**, **Dynamic Resume Parsing**, **Context-Aware Adaptive Questioning**, and **Strict Technical Scoring with Comprehensive Final Reports**.

---

## ⚡ Quick Start (One Command)

```bash
chmod +x start.sh
./start.sh
```

Then open **[http://localhost:5173](http://localhost:5173)** in your browser!

---

## 🛠️ Manual Terminal Setup

### 1. Environment Configuration
Create a `.env` file from the example template:
```bash
cp .env.example .env
```
*(Optional: Add your `DEEPGRAM_API_KEY` or `OPENROUTER_API_KEY`. The platform includes a built-in smart engine that works seamlessly out of the box).*

### 2. Start Backend (Terminal 1)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```
- **Backend URL:** `http://localhost:8000`
- **Swagger API Docs:** `http://localhost:8000/docs`

### 3. Start Frontend (Terminal 2)
```bash
cd client
npm install
npm run dev
```
- **Frontend App:** `http://localhost:5173`

---

## 🎬 Hackathon Reviewer Demo Flow

1. **Upload Resume / Select Role**:
   - Upload any PDF resume or enter a target role (e.g. *Senior Frontend Engineer*, *Machine Learning Engineer*, *DevOps/Cloud Architect*).
   - The platform dynamically extracts the candidate's real name, technical skills, and experience level.
2. **Interactive Voice Interview**:
   - The AI speaks every question aloud with realistic voice modulation.
   - You can click the **🔊 / 🔇** button in the header at any time to toggle or mute audio.
3. **Adaptive Real-Time Probing**:
   - Strong answers dynamically trigger targeted deep-dive follow-ups on specific frameworks and architectures mentioned.
   - Non-answers or weak answers smoothly transition to new domains without getting stuck.
4. **Final Assessment & Report**:
   - Concludes with an in-depth score breakdown (Technical Accuracy, Depth, Clarity, Overall Recommendation, and Actionable Feedback).

---

## 🏗️ Architecture Stack

- **Frontend**: React 18, Vite, Modern Glassmorphism CSS, Web Audio API
- **Backend**: FastAPI (Python 3.11+), SQLite, PyMuPDF (PDF Parser)
- **Voice / Audio**: Deepgram Aura Text-to-Speech
- **LLM / AI Engine**: OpenRouter & Smart Heuristic Multi-Domain Fallback Engine
