# TERRA: Temporal-Evolution and Reasoning-Trace RAG

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active_Development-orange.svg?style=for-the-badge)]()

> **TERRA** (Temporal-Evolution and Reasoning-Trace Retrieval-Augmented Generation) is an advanced RAG framework designed for temporal graph analytics, multi-hop reasoning trace indexation, and automated LLM benchmark evaluation.

---

> [!NOTE]
> 🚧 **ACTIVE RESEARCH & DEVELOPMENT / WORK IN PROGRESS (WIP)**  
> This repository is currently under active development. Algorithms, benchmark datasets, and evaluation scripts will be updated continuously as research progresses.

---

## 📌 Key Architectural Features

- ⏳ **Temporal Evolution Indexing**: Tracks entity relationships, state transitions, and temporal intervals across structured knowledge graphs (`terra_eeg_index.json`).
- 🧠 **Reasoning-Trace Extraction**: Captures intermediate reasoning pathways during complex RAG retrieval cycles (`ask_terra.py`, `view_traces.py`).
- 📊 **Dual Graph & Vector Retrieval**: Combines semantic embedding similarity (ChromaDB) with topological graph analytics (`graph_analytics.py`, `audit_graph.py`).
- 🧪 **Automated Benchmark Harness**: Built-in multi-phase evaluation pipelines (`eval_terra.py`, `rejudge_failed.py`, `stress_test.py`).

---

## 🔐 Environment Setup & API Key Configuration

> [!IMPORTANT]
> All local credentials and secret API keys are kept in your local .env file and ignored from Git version control.

### Step 1: Create .env from Template
```bash
cp .env.example .env
```

### Step 2: Configure Environment Keys
Add your LLM API keys to .env:
```env
# Gemini API Key for LLM trace generation and evaluation
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API Key (Optional)
GROQ_API_KEY=your_groq_api_key_here

# Google LLM Judge API Key
GOOGLE_JUDGE_API_KEY=your_google_judge_api_key_here
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Ingest Data & Build Knowledge Graph
```bash
python ingest_and_build.py
```

### 3. Run TERRA Query Engine
```bash
python ask_terra.py
```

### 4. Execute Benchmark Evaluation
```bash
python eval_terra.py
```

---

## 📁 Repository Architecture

```
TERRA/
├── app.py                   # Streamlit / Web UI Dashboard
├── ask_terra.py             # CLI Query & Inference Entrypoint
├── eval_terra.py            # Multi-Phase Evaluation Pipeline
├── ingest_and_build.py      # Graph Construction & Embedding Ingestion
├── graph_analytics.py       # Topological Graph Analytics & Metrics
├── audit_graph.py           # Graph Verification & Auditing
├── methodology.md           # Research Framework & Theoretical Formulation
├── requirements.txt         # Project Dependencies
└── .env.example             # Environment Secret Placeholder Template
```

---

## 👨‍💻 Authors & Contributors

Developed & Maintained by:
- **Md. Emam Zafor Saadik** ([@zaforsaadik7](https://github.com/zaforsaadik7))
- **Muhammad Raihan Molla** ([@raihan12121](https://github.com/raihan12121))

---

## 📜 License

This repository is open-source under the [MIT License](LICENSE).
