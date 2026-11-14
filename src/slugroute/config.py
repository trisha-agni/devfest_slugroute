# define global paths, constants
# external imports
from dotenv import load_dotenv
from pathlib import Path
import os
# internal imports

# automatically loads .env from project root
load_dotenv()
# read the env variable for api key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# artifacts
COURSE_DATA_FILE = RAW_DATA_DIR / "courses.jsonl"
INDEX_FILE = PROCESSED_DATA_DIR / "course_index.pt"
GRAPH_FILE = PROCESSED_DATA_DIR / "prereq_graph.json"
COURSE_DATA_ENCODING = "utf-8"

# ml models
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
GEMINI_MODEL_NAME = "gemini-3.5-flash"
FALLBACK_MODELS = ["gemini-3.5-flash-lite"]
TOP_K_RETRIEVAL = 5

# env secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ensure runtime dirs exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
