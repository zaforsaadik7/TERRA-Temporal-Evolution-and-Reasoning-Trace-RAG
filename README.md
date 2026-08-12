# TERRA: Temporal-Evolution and Reasoning-Trace RAG

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange?style=for-the-badge)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

> **TERRA** (Temporal-Evolution and Reasoning-Trace Retrieval-Augmented Generation) is a three-stage, closed-loop GraphRAG system for legal reasoning. It routes queries by complexity, traverses a citation graph of 400 SCOTUS cases using BFS, grades retrieved context for entailment, and only then generates a grounded answer — refusing to answer if the context isn't sufficient.

> [!NOTE]
> **TERRA (Mini Dataset Edition)**: This repository hosts the lightweight, self-contained demonstration edition of the TERRA GraphRAG architecture (comprising 34 curated SCOTUS landmark decisions + 366 synthetic cases, total 400 nodes and 726 citation edges). It is specifically optimized for local benchmarking, reproducible evaluation, and academic verification of the IEEE manuscript.

---

## What This Project Actually Does (Plain English)

Imagine you ask: *"How did the Supreme Court's stance on racial segregation evolve from Plessy v. Ferguson to Brown v. Board of Education?"*

A regular AI would answer from memory and might hallucinate details. TERRA instead:
1. **Figures out the question is complex** (Traffic Cop Router calls it `HARD`)
2. **Searches a database** of 400 legal case summaries to find the most relevant ones (ChromaDB vector search)
3. **Follows citation links** between cases — like a trail of breadcrumbs through the citation graph — to pull in related cases you didn't even mention (BFS graph traversal)
4. **Checks whether the retrieved material actually answers the question** before generating anything (NLI Smart Grader)
5. **Refuses to answer** if the material isn't sufficient — instead of making something up
6. **Only then writes the answer**, using only what was retrieved — nothing from memory

---

## Before You Begin: What You Need

You need three things before you touch any code:

### 1. Python 3.10 or newer

Python is the programming language this project runs on. To check if you have it:

**Windows:**
```
Win + R → type cmd → press Enter
```
In the black terminal window that opens, type:
```
python --version
```
You should see something like `Python 3.11.4`. If you see `Python 3.9.x` or older, or if it says "not recognized", you need to install Python.

**Install Python (if needed):**
Go to https://www.python.org/downloads/ and download the latest version. During installation, **check the box that says "Add Python to PATH"** — this is the most commonly missed step that causes problems later.

After installing, close and reopen your terminal, then run `python --version` again to confirm.

### 2. Git (to download the project)

Git is a tool for downloading code from GitHub. To check:
```
git --version
```
If it says "not recognized", install Git from https://git-scm.com/downloads. The default installation settings are fine.

### 3. A Google Gemini API Key (Free)

This project uses Google's Gemini AI model. You need a free API key to use it. Here's exactly how to get one:

1. Go to **https://aistudio.google.com/**
2. Sign in with any Google account
3. Click **"Get API Key"** in the top left
4. Click **"Create API Key"**
5. It will show you a long string starting with `AIza...` — **copy this and save it somewhere** (Notepad is fine). You'll need it in a few minutes.

> **Why do you need two API keys?**
> This project uses one key (`GEMINI_API_KEY`) to generate answers, and a second key (`GOOGLE_JUDGE_API_KEY`) to evaluate how good those answers are. Using the same key for both would be like asking someone to grade their own exam — the results would be biased. Using two separate keys, even from the same account, means the judge call and the generation call go through different quota buckets, which is more honest evaluation. You can create a second API key from the same Google AI Studio page.

---

## Step 1: Download the Project

Open a terminal (Command Prompt or PowerShell on Windows). Navigate to where you want the project to live. For example, to put it on your Desktop:

```
cd Desktop
```

Now clone (download) the repository:

```
git clone https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG.git
```

This creates a folder called `TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG` on your Desktop. Navigate into it:

```
cd TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG
```

From this point forward, **every command in this guide must be run from inside this folder.** If you close and reopen your terminal later, you'll need to `cd` back into this folder before running anything.

---

## Step 2: Check Whether the Pre-Built Data Is Included

This project has two critical data files that the AI needs to answer questions:

- **`terra_eeg_index.json`** — The citation graph (400 cases connected by their legal citations)
- **`terra_vector_db/`** — The vector database (summaries of all 400 cases stored as searchable embeddings)

Check if they're there:

**Windows:**
```
dir terra_eeg_index.json
dir terra_vector_db
```

**Two possible situations:**

**Situation A — Files exist (most likely for this repo):**
You'll see `terra_eeg_index.json` listed (about 325 KB) and a `terra_vector_db` folder. This means the pre-built database is included. **Skip directly to Step 4.** You do NOT need to rebuild anything.

**Situation B — Files are missing:**
You'll see "File Not Found". This means you're starting from scratch and need to build the database yourself. Continue reading Step 3 first, then come back for Step 3B after setting up your environment.

---

## Step 3: Create a Python Virtual Environment

A virtual environment is an isolated box for Python packages. Think of it like this: your computer might have different projects that need different versions of the same software. A virtual environment lets each project have its own private copy of everything it needs, so they don't conflict with each other.

**Create the virtual environment** (this only needs to be done once):

```
python -m venv venv
```

This creates a folder called `venv/` inside your project folder. It contains a private Python installation.

**Now activate the virtual environment:**

```
venv\Scripts\activate
```

You'll know it worked because your terminal prompt will change — it will now show `(venv)` at the beginning:
```
(venv) C:\Users\YourName\Desktop\TERRA-...>
```

> **Important:** Every time you open a new terminal window to work on this project, you must run `venv\Scripts\activate` again. The `(venv)` prefix disappears when you close the terminal. If you forget to activate it and try to run the project, Python won't find the installed packages and will throw `ModuleNotFoundError`.

---

## Step 4: Install the Required Python Packages

Now that the virtual environment is active (you see `(venv)` in your prompt), install all the packages this project needs:

```
pip install -r requirements.txt
```

This reads the `requirements.txt` file and automatically downloads and installs all 15 libraries. Here's what they do so you understand why they're there:

| Package | What it does in this project |
|---|---|
| `google-genai` | Talks to Google's Gemini API to generate answers and run the NLI judge |
| `chromadb` | The vector database — stores case summaries and lets us search them by meaning |
| `networkx` | Handles the citation graph — nodes are cases, edges are "Case A cited Case B" |
| `datasets` | Downloads datasets from Hugging Face (used during ingestion) |
| `eyecite` | Parses legal citation strings like "347 U.S. 483" from text |
| `pandas` | Handles tabular data for the evaluation results |
| `tqdm` | Shows progress bars during long operations |
| `tabulate` | Formats results into clean tables for the evaluation report |
| `fastapi` | The web server framework — serves the dashboard and the `/query` API |
| `uvicorn` | Runs the FastAPI server (FastAPI needs this to actually start) |
| `python-dotenv` | Reads your `.env` file so the code can find your API keys |
| `pydantic` | Validates that API inputs and outputs have the right structure |
| `rouge-score` | Computes ROUGE-L scores (a text similarity metric that doesn't need an LLM) |
| `requests` | Makes HTTP requests (used in some utility scripts) |
| `scipy` | Runs the Wilcoxon statistical significance tests on evaluation results |

This will take 2–5 minutes. You'll see a lot of text scrolling — that's normal.

**If you get an error about `eyecite`:** This is a known issue on some Windows machines because `eyecite` depends on a compiled C++ library. The project has already worked around this internally, so just let the error pass — it should still install successfully enough to work.

---

## Step 5: Configure Your API Keys

The project reads your API keys from a file called `.env`. This file is never uploaded to GitHub (it's in `.gitignore`) so you have to create it yourself on your machine.

A template file called `.env.example` is already in the project folder. **Make a copy of it and rename the copy to `.env`:**

**Windows:**
```
copy .env.example .env
```

Now open the `.env` file in any text editor (Notepad works fine):

```
notepad .env
```

You'll see this:
```
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_JUDGE_API_KEY=your_google_judge_api_key_here
```

Replace the placeholder text with your actual keys:
```
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_JUDGE_API_KEY=AIzaSyCyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

**Rules for this file:**
- No spaces around the `=` sign
- No quotation marks around the key values
- Each key goes on its own line
- Do not share this file with anyone — it's your private credential

Save the file and close Notepad.

**To verify it was saved correctly:**
```
type .env
```
You should see your keys printed in the terminal (without any `your_..._here` placeholders).

---

## Step 3B: Build the Database from Scratch (Only if Step 2 said files are missing)

> **Skip this section entirely if you found `terra_eeg_index.json` and `terra_vector_db/` in Step 2. Jump to Step 6.**

If the pre-built database is not included, you need to run the ingestion pipeline. This script downloads the source legal cases, extracts citation links, generates AI-written summaries for each case, and stores everything in the graph and vector database.

**Make sure your virtual environment is active and your `.env` is configured before running this.**

```
venv\Scripts\python ingest_and_build.py
```

**What this does, step by step:**
1. Loads 34 real curated SCOTUS cases (hardcoded) + generates 366 synthetic stress-test cases
2. For each case, uses Gemini to write a structured "thinking trace" — a bullet-point legal reasoning summary
3. Stores those traces in ChromaDB (`terra_vector_db/`) as vector embeddings
4. Parses citation strings from case texts using `eyecite`
5. Builds the citation graph and saves it to `terra_eeg_index.json`

**How long will it take?** The LLM calls are rate-limited to avoid hitting Google's free tier limits. Expect **30–90 minutes** for the full 400-case build. You'll see a progress bar.

**If it crashes midway:** Just run the command again. The script checks what's already been saved and resumes from where it left off.

After it finishes, you should see:
- `terra_eeg_index.json` (about 325 KB)
- A `terra_vector_db/` folder containing several UUID-named subfolders and a `chroma.sqlite3` file

---

## Step 6: Start the TERRA Server (The Main Way to Run the Project)

Everything is set up. Now start the project:

```
venv\Scripts\python app.py
```

You will see output like this:
```
[WARNING] AWS_BEARER_TOKEN_BEDROCK not set in .env — Bedrock inference path disabled. Only the Gemini client path will be active.
Loading graph index from terra_eeg_index.json...
Graph loaded: 400 nodes, 726 edges
ChromaDB collection loaded: 400 documents
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The `[WARNING]` about Bedrock is **normal and harmless** — that's a backup inference backend that's disabled. The important lines are the ones showing the graph loaded and the server started.

**Now open your web browser** and go to:

```
http://127.0.0.1:8000
```

You will see the TERRA GraphRAG Dashboard — a dark-mode interface where you can type legal questions and get answers.

**To stop the server:** Press `Ctrl + C` in the terminal.

---

## Step 7: Using the Dashboard

The dashboard has a text box in the center. Type a question related to U.S. civil rights constitutional law and press Enter or click Search.

**Questions the system is designed to answer (in-domain):**
- *"What was the separate but equal doctrine established by Plessy v. Ferguson?"*
- *"How did graduate school desegregation cases influence the Brown ruling?"*
- *"What constitutional amendment did Brown v. Board of Education rely on?"*
- *"In what year was Sweatt v. Painter decided and what did it rule?"*

**Questions the system is designed to refuse (out-of-domain):**
- *"What was the decision in Roe v. Wade?"* — not in the indexed domain
- *"How do you calculate the area of a circle?"* — completely unrelated
- *"What did the Court rule in Citizens United v. FEC?"* — different legal domain

When the system refuses, that is **correct behavior** — it means the safety firewall is working. It would rather say "I don't have enough verified information" than make something up.

**What the response shows you:**
- **Route badge** — either `EASY` (answered directly) or `HARD` (went through the full graph pipeline)
- **Answer** — the grounded legal response
- **Context** — the thinking traces that were retrieved and used to generate the answer
- **Latency** — how long each stage took

---

## Step 8: Using the API Directly (Optional, For Developers)

The dashboard is a wrapper around a JSON API. You can call it directly if you want to integrate TERRA into another application.

**Open a second terminal window** (keep the server running in the first one).

**Query endpoint:**
```
curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d "{\"query\": \"What doctrine did Plessy v. Ferguson establish?\"}"
```

**Explainability endpoint** (shows which cases were retrieved and which edges were traversed):
```
curl -X POST "http://127.0.0.1:8000/explain" -H "Content-Type: application/json" -d "{\"query\": \"What doctrine did Plessy v. Ferguson establish?\"}"
```

**Case detail endpoint** (fetch a specific case by its ID):
```
curl "http://127.0.0.1:8000/case/C007"
```

**Interactive API docs** (auto-generated by FastAPI — lists every endpoint with a form to test them):
```
http://127.0.0.1:8000/docs
```

---

## Step 9: Running the Evaluation Benchmark (Optional)

The 35-query evaluation has already been run and its results are saved in `terra_eval_raw.json` and `terra_evaluation_report.md`. You do NOT need to re-run it to use the project. But if you want to reproduce the results yourself:

> **Warning:** Re-running the full evaluation makes approximately **315 Gemini API calls** (35 queries × 3 pipelines × 3 calls each). On the free tier, this will take **2–4 hours** due to rate limiting. The script handles this automatically with retry/sleep logic.

```
venv\Scripts\python run_full_eval.py
```

This runs three phases:
1. **Generation** — runs all 35 queries through all 3 pipelines (Direct LLM, Flat RAG, TERRA GraphRAG) and saves answers to `terra_generations.json`
2. **Judging** — sends each answer to an LLM judge that scores faithfulness and relevance, saves to `terra_eval_raw.json`
3. **Report** — computes ROUGE-L scores, Wilcoxon significance tests, and writes the final `terra_evaluation_report.md`

If the script crashes midway due to a rate limit or network error, just run the same command again — it resumes from where it left off.

**To just view the pre-computed results without re-running anything:**
```
type terra_evaluation_report.md
```

---

## Step 10: Running the Safety Firewall Stress Test (Optional)

This test sends 15 deliberately out-of-domain and adversarial queries through the system to verify the safety rejection rate:

```
venv\Scripts\python stress_test.py
```

Expected output: **15/15 rejections (100% safety rejection rate)**. Each query prints whether it was correctly rejected. This test takes about 5–10 minutes.

---

## Step 11: Inspecting the Knowledge Base (Optional)

To see all 400 thinking traces stored in the ChromaDB vector database (prints each case's ID, title, and reasoning summary):

```
venv\Scripts\python view_traces.py
```

To run a connectivity audit on the citation graph (shows node count, edge count, degree distribution, and a node-by-node connectivity table):

```
venv\Scripts\python audit_graph.py
```

---

## Troubleshooting

### ❌ `ModuleNotFoundError: No module named 'google'` (or any other module)

This means the virtual environment is not activated. Run:
```
venv\Scripts\activate
```
Then try the command again. You must see `(venv)` in your prompt before running any Python files.

---

### ❌ `KeyError: 'GEMINI_API_KEY environment variable is not set'`

The `.env` file is missing, empty, or has the wrong key name. Check:
```
type .env
```
You should see `GEMINI_API_KEY=AIza...` with your actual key. If it still says `your_gemini_api_key_here`, you forgot to edit the file. If the file doesn't exist at all, run `copy .env.example .env` and then edit it.

---

### ❌ `Collection 'thinking_traces' does not exist` or `Graph index not found`

The pre-built database files are missing. Either:
- The `terra_vector_db/` folder is not in the project directory
- The `terra_eeg_index.json` file is missing

You need to run the ingestion pipeline (Step 3B). Check Step 2 to confirm the files are missing.

---

### ❌ The server starts but gives wrong answers or always refuses

This usually means the ChromaDB collection it loaded is the wrong one. The project has two ChromaDB directories:
- `terra_vector_db/` — the main, correct, 400-case database ✅
- `chroma_db/` — an old legacy database from an earlier phase ❌

`ask_terra.py` is configured to use `terra_vector_db/`. If you accidentally moved or renamed it, the system will fail silently. Check that the `terra_vector_db/` folder exists and contains a `chroma.sqlite3` file that is larger than 8 MB.

---

### ❌ Rate limit errors during evaluation (`429 RESOURCE_EXHAUSTED`)

This is normal behavior on Google's free Gemini tier. The scripts automatically sleep and retry. You don't need to do anything — just let it run. If you see a lot of `Sleeping for 10s before retry` messages, the script is handling it. The evaluation will be slow (2–4 hours) but will complete.

---

### ❌ `eyecite` installation fails with a C++ compiler error

This is a known Windows issue. Run the installation with `--no-deps` flag for eyecite:
```
pip install -r requirements.txt --ignore-installed eyecite
pip install eyecite --no-deps
```
The core functionality (citation search in graph traversal) still works through the runtime mock that the code applies automatically.

---

## File Reference: What Each File Does

| File | What it does | Do you need to run it? |
|---|---|---|
| `app.py` | FastAPI server + dark-mode dashboard UI | **Yes** — this is how you use TERRA |
| `ask_terra.py` | Core inference engine (Traffic Cop → BFS → NLI Grader → Generator) | Auto-imported by `app.py` |
| `ingest_and_build.py` | Builds the graph and vector DB from scratch | Only if database files are missing |
| `eval_terra.py` | 35-query benchmark suite (imported by `run_full_eval.py`) | No — pre-run, results already saved |
| `run_full_eval.py` | Runs the full evaluation pipeline end-to-end | Only to reproduce results |
| `graph_analytics.py` | Computes network metrics on the citation graph | No — results already in `terra_graph_metrics.json` |
| `stress_test.py` | Safety firewall stress test (15 queries) | Optional |
| `audit_graph.py` | Graph connectivity audit | Optional diagnostic |
| `rejudge_failed.py` | Re-judges any records with suspicious scores | Only if you spot bad scores after re-running eval |
| `final_eval_run.py` | Alternate eval runner with unique output filenames | Only during active development |
| `view_traces.py` | Prints all ChromaDB thinking traces | Optional inspection tool |

| Data File | What it contains | Safe to delete? |
|---|---|---|
| `terra_eeg_index.json` | The serialized citation graph (400 nodes, 726 edges) | **No** — deleting breaks the server |
| `terra_vector_db/` | ChromaDB persistent store (400 thinking traces, ~9 MB) | **No** — deleting breaks the server |
| `terra_eval_raw.json` | Full raw evaluation results (105 records) | Yes, but you'll lose the results |
| `terra_generations.json` | All pipeline generation outputs | Yes, but you'll need to re-run eval |
| `terra_graph_metrics.json` | Computed graph statistics | Yes, can be regenerated with `graph_analytics.py` |
| `terra_evaluation_report.md` | Final benchmark report table | Yes, can be regenerated |

---

## Academic Attribution

**Md. Emam Zafor Saadik** ([@zaforsaadik7](https://github.com/zaforsaadik7))  
Bangladesh University of Business and Technology (BUBT) — Department of CSE

For the full methodology, see [`methodology.md`](methodology.md).  
For paper writing guidance, see [`paper_readiness_analysis.md`](paper_readiness_analysis.md) and [`q1_journal_readiness.md`](q1_journal_readiness.md).

---

## License

Open-source under the [MIT License](LICENSE).
