# External imports
from bs4 import BeautifulSoup, Tag
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib.parse import urldefrag, urljoin
from urllib3.util.retry import Retry
import json
import re
import requests
import threading
# Internal imports
from slugroute.config import (
  COURSE_DATA_FILE,
  COURSE_DATA_ENCODING,
)

BASE_CATALOG_URL = "https://catalog.ucsc.edu/en/current/general-catalog/courses"
COURSE_URL_SUBSTR = "/en/current/general-catalog/courses/"
MAX_WORKERS = 32
REQUEST_TIMEOUT = 15

CODE_RE = re.compile(r"^([A-Z]{2,5}(?:\s+[A-Z]{2,4})?)\s+(\d+[A-Z]?)$")
HEADING_RE = re.compile(r"^([A-Z]{2,5}(?:\s+[A-Z]{2,4})?\s+\d+[A-Z]?)\s*[-–—:]?\s*(.*)$")
PREREQ_DESC_RE = re.compile(
  r"(?:Prerequisite\(s\):|Prerequisites?:)\s*(.*?)(?=\.\s+[A-Z]|\.$|$)",
  re.IGNORECASE,
)

CODE_KEY = 'code'
SUB_KEY = 'subject'
NUM_KEY = 'number'
TITLE_KEY = 'title'
CREDITS_KEY = 'credits'
DESC_KEY = 'desc'
PREREQ_KEY = 'prereq_raw'
GENED_KEY = 'gen_ed'
REP_KEY = 'repeatable'
URL_KEY = 'url'

thread_local = threading.local()


def get_session():
  if not hasattr(thread_local, "session"):
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(pool_connections=MAX_WORKERS,
                                    pool_maxsize=MAX_WORKERS,
                                    max_retries=retries))
    thread_local.session = s
  return thread_local.session


def _clean(txt):
  text = ' '.join(txt.split())
  replacements = {
    " ,": ",",
    " .": ".",
    " ;": ";",
    " :": ":",
    " )": ")",
    "( ": "(",
  }
  for old, new in replacements.items():
    text = text.replace(old, new)
  return text


def _discover_urls(base_url: str) -> set[str]:
  try:
    resp = get_session().get(base_url, timeout=REQUEST_TIMEOUT)
    soup = BeautifulSoup(resp.text, "html.parser")
    urls = set()
    for a in soup.select("a[href]"):
      full_url = urljoin(base_url, a["href"])
      clean_url, _ = urldefrag(full_url)
      if COURSE_URL_SUBSTR in clean_url:
        urls.add(clean_url)
    return urls
  except Exception:
      return set()


def _parse_course_page(url: str) -> dict | None:
  try:
    resp = get_session().get(url, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
      return None
    resp.encoding = COURSE_DATA_ENCODING
    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.select_one("main") or soup.body or soup

    # 1. Parse & validate Course Code
    h1 = main.find("h1")
    if not h1:
      return None
    heading_text = _clean(h1.get_text(" ", strip=True))
    match = HEADING_RE.match(heading_text)
    if not match:
      return None

    raw_code, title = match.group(1).strip(), match.group(2).strip()
    code_match = CODE_RE.match(raw_code)
    if not code_match:
      return None

    subject, number_str = code_match.group(1), code_match.group(2)

    # 2. Parse Description
    desc_el = main.select_one(".desc")
    desc = _clean(desc_el.get_text(" ", strip=True)) if desc_el else ""

    # 3. Parse Metadata & Extra Fields
    gen_ed = None
    gened_el = main.select_one(".genEd")
    if gened_el:
      tokens = _clean(gened_el.get_text(" ", strip=True)).split()
      if tokens:
        gen_ed = tokens[-1]

    extra_fields = {}
    for field in main.select("div.extraFields"):
      h = field.find(["h2", "h3", "h4", "h5", "h6"])
      if not h:
        continue
      vals = [_clean(c.get_text(" ", strip=True))
              for c in field.children
              if isinstance(c, Tag) and c != h]
      key = _clean(h.get_text(" ", strip=True)).lower()
      extra_fields[key] = " ".join(filter(None, vals))

    # 4. Extract Credits & Repeatability
    credits_val = None
    for k in ["credits", "credit"]:
      if k in extra_fields:
        digit_match = re.search(r"\d+", extra_fields[k])
        if digit_match:
          credits_val = int(digit_match.group())
          break

    repeatable = "yes" in extra_fields.get("repeatable for credit", "").lower()

    # Extract raw prerequisites / requirements
    prereq_raw = extra_fields.get("requirements", "") or \
      extra_fields.get("prerequisite(s)", "")
    if not prereq_raw and "prerequisite" in desc.lower():
      # in some cases the prerequisites are placed inside the description text
      # e.g. "Prerequisite(s): ANTH 1 and ANTH 104."
      m = PREREQ_DESC_RE.search(desc)
      if m:
        prereq_raw = m.group(0).strip().rstrip(".") + "."

    return {
      CODE_KEY: raw_code,
      SUB_KEY: subject,
      NUM_KEY: number_str,
      TITLE_KEY: title or raw_code,
      CREDITS_KEY: credits_val,
      DESC_KEY: desc,
      PREREQ_KEY: prereq_raw,
      GENED_KEY: gen_ed,
      REP_KEY: repeatable,
      URL_KEY: url,
    }
  except Exception:
    return None


def run_pipeline():
  COURSE_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
  print(f"discovering departments from {BASE_CATALOG_URL}...")
  dept_urls = _discover_urls(BASE_CATALOG_URL)
  print(f"found {len(dept_urls)} department pages.")

  print("discovering course links...")
  course_urls = set()
  with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(_discover_urls, url) for url in dept_urls]
    for f in as_completed(futures):
      course_urls.update(f.result())

  print(f"found {len(course_urls)} candidate urls. scraping courses...")
  unique_courses: dict[str, dict] = {}
  lock = threading.Lock()
  completed = 0

  with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(_parse_course_page, url): url for url in course_urls}
    for f in as_completed(futures):
      data = f.result()
      with lock:
        completed += 1
        if data and data["code"] not in unique_courses:
          unique_courses[data["code"]] = data
        if completed % 500 == 0:
          print(f"processed {completed}/{len(course_urls)} urls "
                f"(found {len(unique_courses)} valid courses)...")

  # Sort & Save to JSONL
  sorted_courses = sorted(unique_courses.values(), key=lambda x: x["code"])
  with open(COURSE_DATA_FILE, "w", encoding="utf-8") as f:
    for c in sorted_courses:
      f.write(json.dumps(c, ensure_ascii=False) + "\n")

  print(f"saved {len(sorted_courses)} courses to {COURSE_DATA_FILE}")


if __name__ == "__main__":
  run_pipeline()
