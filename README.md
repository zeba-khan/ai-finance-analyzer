# 💰 AI Finance Analyzer

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-yellow)

> A full-stack AI-powered personal finance tracker with ML category prediction, anomaly detection, and a RAG-based conversational AI assistant — built with FastAPI, PostgreSQL, scikit-learn, ChromaDB, and Groq LLM.

---

## 🚀 Live Demo
*Coming soon — run locally with Docker (see Quick Start below)*

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│  Dashboard │ Add Transaction │ Upload CSV │ AI Chat │ Manage │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                           │
│  /transactions  │  /chat  │  /analytics                     │
│                                                             │
│  ┌─────────────────┐   ┌──────────────────────────────┐    │
│  │  ML Pipeline    │   │       RAG Pipeline            │    │
│  │                 │   │                              │    │
│  │ Naive Bayes +   │   │  sentence-transformers       │    │
│  │ TF-IDF          │   │  → ChromaDB (vector store)   │    │
│  │ (category)      │   │  → Groq LLaMA3 (LLM)         │    │
│  │                 │   │                              │    │
│  │ Isolation       │   └──────────────────────────────┘    │
│  │ Forest          │                                        │
│  │ (anomalies)     │                                        │
│  └─────────────────┘                                        │
│                                                             │
│  SQLAlchemy ORM                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   PostgreSQL Database                        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Tech Used |
|---|---|
| Auto transaction categorization | Naive Bayes + TF-IDF |
| Anomaly detection & alerts | Isolation Forest |
| Conversational AI over your data | LangChain + ChromaDB + Groq LLaMA3 |
| CSV bank statement import | pandas + custom parser |
| Interactive dashboard | Plotly + Streamlit |
| REST API with validation | FastAPI + Pydantic |
| Containerized deployment | Docker + docker-compose |

---

## 🛠️ Tech Stack

**Backend:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL  
**ML:** scikit-learn (Naive Bayes, Isolation Forest), joblib  
**RAG:** sentence-transformers, ChromaDB, Groq API (LLaMA3)  
**Frontend:** Streamlit, Plotly  
**DevOps:** Docker, docker-compose, Render

---

## ⚡ Quick Start (Local)

### Prerequisites
- Python 3.11+
- PostgreSQL running locally
- (Optional) Groq API key from [console.groq.com](https://console.groq.com) — free tier available

### 1. Clone & setup

```bash
git clone https://github.com/zeba-khan/ai-finance-analyzer
cd ai-finance-analyzer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your PostgreSQL credentials and Groq API key
```

### 3. Run backend

```bash
cd backend
uvicorn main:app --reload
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 4. Run frontend (new terminal)

```bash
streamlit run streamlit_app.py
# App running at http://localhost:8501
```

---

## 🐳 Docker (Recommended)

```bash
# Copy env file
cp backend/.env.example backend/.env
# Add your GROQ_API_KEY to .env

# Start everything
docker-compose up --build

# App: http://localhost:8501
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/transactions/` | Create transaction |
| GET | `/transactions/` | Get all with anomaly scores |
| PUT | `/transactions/{id}` | Update transaction |
| DELETE | `/transactions/{id}` | Delete transaction |
| POST | `/transactions/upload/csv` | Bulk CSV import |
| POST | `/chat/` | RAG chat query |
| GET | `/analytics/summary` | KPI summary |
| GET | `/analytics/by-category` | Spending by category |
| GET | `/analytics/by-month` | Monthly trend |

---

## 🤖 How the RAG Chat Works

1. Every transaction is embedded using `sentence-transformers/all-MiniLM-L6-v2`
2. Embeddings are stored in ChromaDB (persistent local vector store)
3. When you ask a question, the question is embedded and top-N similar transactions are retrieved
4. Retrieved transactions are passed as context to Groq's LLaMA3-8B model
5. LLM answers based only on your actual data — no hallucinations

---

## 🚀 Deploy to Render

1. Push to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Set build command: `pip install -r requirements.txt`
4. Set start command:  uvicorn main:app --host 0.0.0.0 --port $PORT
5. Add environment variables from your `.env`
6. Create a free PostgreSQL database on Render and link it

---

## 📁 Project Structure

```
ai-finance-analyzer/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables (never commit!)
│   └── app/
│       ├── config.py              # Settings (pydantic-settings)
│       ├── database.py            # SQLAlchemy engine + session
│       ├── models/
│       │   └── transaction.py     # DB table definition
│       ├── schemas/
│       │   └── transaction.py     # Pydantic request/response models
│       ├── routes/
│       │   ├── transactions.py    # CRUD + CSV upload endpoints
│       │   ├── chat.py            # RAG chat endpoint
│       │   └── analytics.py      # Dashboard stats endpoints
│       ├── services/
│       │   └── transaction_service.py  # Business logic
│       ├── crud/
│       │   └── transaction_crud.py     # DB queries
│       ├── ml/
│       │   ├── classifier.py      # Naive Bayes category predictor
│       │   ├── anomaly.py         # Isolation Forest detector
│       │   └── rag_engine.py      # ChromaDB + Groq RAG pipeline
│       └── utils/
│           └── csv_parser.py      # Multi-format CSV parser
├── streamlit_app.py               # Full frontend (5 pages)
├── Dockerfile.backend
├── Dockerfile.frontend
└── docker-compose.yml

```

---

## 📄 License
MIT
