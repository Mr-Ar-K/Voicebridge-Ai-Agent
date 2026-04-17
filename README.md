# 🎙️ VoiceBridge AI

VoiceBridge AI is a multilingual voice-enabled assistant that helps users discover relevant Indian government schemes using natural language.

Users can ask questions through voice or text about schemes related to students, farmers, jobs, healthcare, and more.

The system retrieves accurate scheme information using semantic search and AI reasoning.

---

## 🚀 Features

- 🎤 Voice interaction using Vapi AI
- 🧠 AI-powered scheme retrieval
- 🌐 Multilingual support (English + Indian languages)
- ⚡ FastAPI backend for real-time processing
- 🔎 Qdrant vector database for semantic search
- 📊 Structured JSON responses
- 💻 Clean and responsive UI
- 🗣️ Natural language understanding

---

## 🧩 Problem Solved

Finding the right government scheme is difficult because:

- Information is scattered across multiple websites
- Language barriers prevent accessibility
- Users do not know which schemes they are eligible for
- Government portals are complex to navigate

VoiceBridge AI simplifies access to schemes using conversational AI.

---

## 🏗️ Architecture

User Voice/Text  
↓  
Vapi Voice Agent  
↓  
FastAPI Backend  
↓  
Groq LLM reasoning  
↓  
Qdrant Vector Database  
↓  
Structured Response  
↓  
Frontend UI  

---

## 🛠️ Tech Stack

Backend:
- FastAPI
- Python

AI:
- Groq LLM
- Qdrant Vector Database
- Embeddings API

Voice:
- Vapi AI

Frontend:
- HTML
- CSS
- JavaScript

---

## 📂 Project Structure


Voicebridge-Ai-Agent
│
├── backend
│ ├── main.py
│ ├── requirements.txt
│
├── frontend
│ └── index.html
│
├── knowledge.json
├── README.md


---

## ▶️ How to Run

### Backend

Install dependencies:


pip install -r requirements.txt


Run server:


uvicorn main:app --reload


---

### Frontend

Open file:


frontend/index.html


---

## 💡 Example Queries

- student schemes
- farmer schemes
- scholarships for degree students
- government schemes for unemployed youth
- health schemes for poor families

---

## 🔮 Future Improvements

- context-aware conversations
- regional language optimization (Telugu, Hindi, Tamil)
- real-time scheme updates from government APIs
- personalized recommendations
- eligibility checker
- WhatsApp bot integration
- mobile app version
- speech-to-speech responses
- dashboard analytics
- integration with DigiLocker
- 22+ Indian language support

---

## 📈 Scalability

VoiceBridge AI can scale to:

- rural information centers
- government help kiosks
- WhatsApp chatbots
- IVR phone systems
- mobile applications
- citizen service portals

---

## 👥 Team

Team Name: gamma geeks3

Team Leader:
M. Madhu Nikhil

---

## 🏁 Hackathon Submission

Built for HackBLR Hackathon.

Using:
Vapi + Qdrant + AI Agents