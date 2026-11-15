# 🌲 SlugRoute | UCSC AI Academic Advisor & Pathway Simulator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![NetworkX](https://img.shields.io/badge/graph-NetworkX-green.svg)](https://networkx.org/)

> **"SlugRoute is an AI academic advisor for UCSC students that turns complex prerequisite chains into interactive pathway graphs and personalized graduation roadmaps."**

Built for **UC Santa Cruz GDG DevFest '26**, **SlugRoute** is an intelligent academic advising platform that solves the friction of navigating UCSC's fast-paced 10-week quarter system. It pairs **Directed Acyclic Graph (DAG) algorithms** with **Google Gemini agentic function calling** to deliver hallucination-free, deterministic degree planning and interactive dependency visualization.

---

## 📸 Key Features

### 1. 💬 Grounded AI Academic Advisor
* Powered by **Google Gemini** (`gemini-3.5-flash` / `gemini-2.5-flash`) via the `google-genai` SDK.
* Employs **autonomous tool calling** (`search_courses`, `check_prerequisites`, `generate_roadmap`, `inspect_course`) to ensure advice is 100% grounded in real university catalog data.
* Automatically converts catalog course codes in chat into **clickable, authoritative UCSC catalog links**.

### 2. 🗺️ Deterministic Roadmap Simulator
* Uses **topological DAG scheduling** and greedy credit-load balancing to build quarter-by-quarter pathways.
* Enforces declared major constraints (`CS_BS`, `BME_BS`), customizable quarterly credit ceilings (12–22 units/quarter), and prerequisite precedence.
* Resolves multi-track prerequisite ties (e.g., favoring `MATH 19A/B` for CS majors over Life Sciences `MATH 11A/B`).

### 3. 🕸️ Interactive Prerequisite Network Graph
* Physics-based interactive dependency visualization rendered via **Pyvis** and **vis.js**.
* Supports adjustable search depth (Direct prerequisites up to the complete ancestral tree).
* Styled in official **UCSC Banana Slug Gold** (`#FFD100`) and **UCSC Navy Blue** (`#005596`).

---

## 🏗️ Architecture & Technical Stack

```
SlugRoute Architecture
├── Data Pipeline (Catalog Scraping & Indexing)
│   ├── Beautiful Soup + Requests  ──► Raw Course Catalog (data/raw/courses.jsonl)
│   ├── Prerequisite Parser Regex  ──► Boolean Prereq Graph (data/processed/prereq_graph.json)
│   └── Sentence Transformers      ──► Dense Vector Index (data/processed/course_index.pt)
│
├── Core Engines
│   ├── AcademicGraphEngine        ──► NetworkX DAG, DNF/CNF Validator & Topological Sequencer
│   └── CourseRetriever            ──► Cosine Similarity Vector Search (all-MiniLM-L6-v2)
│
├── Agent Layer
│   └── SlugAdvisor (Gemini)       ──► Autonomous Tool Calling & Reasoning Agent
│
└── Presentation Layer
    └── Streamlit Web App          ──► Dynamic UI with Pyvis Interactive Physics Graph
```

### Technologies Used
* **Languages & Core:** Python 3.11+, JSON, HTML5, CSS3, JavaScript (vis.js).
* **AI & Agentic Framework:** Google Gemini API (`google-genai`), Tool / Function Calling, Prompt Grounding.
* **Graph Theory:** `NetworkX` (DAG validation, ancestral subgraph extraction, topological sort).
* **Vector Search & NLP:** `PyTorch`, `sentence-transformers` (`all-MiniLM-L6-v2`), Semantic Cosine Retrieval.
* **UI & Visualization:** `Streamlit`, `Pyvis`.
* **Data Extraction:** `BeautifulSoup4`, `Requests`.
* **Package Management:** `uv`, `pyproject.toml`.

---

## 📂 Project Structure

```text
devfest_slugroute/
├── app.py                     # Streamlit frontend & interactive tabs
├── pyproject.toml             # Project dependencies and package metadata
├── uv.lock                    # Locked dependency tree
├── .env.example               # Template for environment secrets
│
├── src/slugroute/             # Main Python package
│   ├── config.py              # Global paths, constants, and model definitions
│   ├── agent/
│   │   ├── advisor.py         # Gemini conversational advisor with tool integration
│   │   └── tools.py           # Registered tool definitions callable by Gemini
│   ├── graph/
│   │   └── engine.py          # AcademicGraphEngine: DAGs, DNF logic, tie-breaking
│   └── retriever/
│       └── retriever.py       # Vector embeddings & semantic course search
│
├── data_pipeline/             # Catalog scraping and index generation
│   ├── 01_scrape_courses.py   # Web scraper for UCSC general catalog
│   ├── 02_build_embeddings.py # Vector embedding generator
│   └── 03_build_graph.py      # Prerequisite graph compiler
│
├── data/
│   ├── raw/courses.jsonl      # Scraped catalog courses (4,000+ entries)
│   └── processed/
│       ├── prereq_graph.json  # NetworkX JSON graph representation
│       └── course_index.pt    # PyTorch vector tensor index
│
├── assets/                    # Static branding assets (Banana Slug logo)
└── test_*.py                  # Comprehensive unit & regression test suites
```

---

## ⚡ Prerequisite Resolution & Tie-Breaking

UCSC courses frequently express prerequisites in multi-track **Disjunctive Normal Form (DNF)**:
$$\text{Track}_1 \lor \text{Track}_2 \lor \dots \lor \text{Track}_k$$
Where each track consists of groups joined by logical $\text{AND}$, and each group contains alternative courses joined by logical $\text{OR}$.

In `AcademicGraphEngine`, ties are resolved deterministically based on declared major profiles:
1. **Completed Courses (Cost = 0):** Free if already fulfilled.
2. **Core Major Requirements (Cost = 1):** For `CS_BS`, courses like `CSE 12`, `CSE 13S`, `CSE 16`, `MATH 19A/B`, and `MATH 21`.
3. **Engineering Alternatives (Cost = 3):** E.g., `CSE 13E` or `ECE 13`.
4. **Preferred Department Match (Cost = 5):** Unranked electives within `CSE`, `MATH`, or `AM`.
5. **Non-Major / Deprioritized Tracks (Cost = 8):** E.g., `MATH 11A/B` or `BME 160`.
6. **External Departments (Cost = 10):** Unrelated electives.

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/devfest_slugroute.git
cd devfest_slugroute
```

### 2. Set Up Python Environment
Using [uv](https://github.com/astral-sh/uv) (recommended):
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```
Or standard `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Configure API Keys
Copy the template and add your Google Gemini API key:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running Tests

The test suite validates graph integrity, vector search precision, and Gemini agent tool execution:

```bash
# Verify the prerequisite graph is strictly a Directed Acyclic Graph (DAG)
python test_graph_integrity.py

# Test deterministic roadmap generation and prerequisite evaluation
python test_engine.py

# Test semantic vector course retrieval
python test_retriever.py

# Test autonomous tool execution
python test_tools.py

# Test Gemini API connectivity and live response
python test_advisor.py
```

---

## 🎓 Acknowledgements & Event

Developed for **UCSC GDG DevFest '26** by team SlugRoute.  
Course data scraped from the official [UC Santa Cruz General Catalog](https://catalog.ucsc.edu/).  
Fiat Slug! 🍌
