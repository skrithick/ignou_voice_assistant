import os
import re
import time
import json
import requests
import dotenv

dotenv.load_dotenv()

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"
OUTPUT_DIR = "ignou_markdown"
REQUEST_DELAY_SECONDS = 6.5
MAX_RETRIES = 3

BASE = "https://www.ignou.ac.in"

PAGES = {
    "about_us": [
        (f"{BASE}/pages/2", "about_us_landing"),
        (f"{BASE}/pages/11", "amenities"),
        (f"{BASE}/pages/10", "authorities"),
        (f"{BASE}/pages/12", "awards"),
        (f"{BASE}/pages/17", "cells_units"),
        (f"{BASE}/pages/168", "centers_institutes"),
        (f"{BASE}/pages/14", "chairs"),
        (f"{BASE}/pages/15", "collaboration"),
        (f"{BASE}/pages/16", "divisions"),
        (f"{BASE}/pages/18", "jobs_tenders"),
        (f"{BASE}/pages/20", "profile"),
        (f"{BASE}/pages/21", "projects_consultancy"),
        (f"{BASE}/pages/24", "publications"),
        (f"{BASE}/pages/23", "recognitions"),
        (f"{BASE}/pages/22", "regional_centres"),
        (f"{BASE}/pages/25", "school_of_studies"),
        (f"{BASE}/pages/26", "study_centres"),
    ],
    "employee_services": [
        (f"{BASE}/pages/205", "empanelled_hospitals"),
        (f"{BASE}/pages/207", "guest_house"),
        (f"{BASE}/pages/219", "university_house_allotment"),
        (f"{BASE}/announcement/Career?nav=5", "jobs_at_ignou"),
        (f"{BASE}/announcements/0?nav=6", "announcements"),
        (f"{BASE}/pages/218", "committee_against_sexual_harassment"),
    ],
    "student_services": [
        (f"{BASE}/pages/65", "study_material_status"),
        (f"{BASE}/pages/51", "academic_calendar"),
        (f"{BASE}/pages/64", "faqs"),
        (f"{BASE}/pages/222", "anti_ragging"),
        (f"{BASE}/pages/57", "swayam_prabha")
    ],
}


def slugify(name: str) -> str:
    name = re.sub(r"[^\w\-]+", "_", name.strip())
    return re.sub(r"_+", "_", name).strip("_").lower()


def scrape_url(url: str) -> str:
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
    }

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                FIRECRAWL_SCRAPE_URL, headers=headers, json=payload, timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                markdown = data.get("data", {}).get("markdown", "")
                if not markdown:
                    raise ValueError(f"No markdown returned for {url}: {json.dumps(data)[:300]}")
                return markdown
            elif resp.status_code == 429:
                wait = 5 * attempt
                print(f"  Rate limited on {url}, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            last_err = e
            print(f"  Attempt {attempt} failed for {url}: {e}")
            time.sleep(2 * attempt)

    raise RuntimeError(f"Failed to scrape {url} after {MAX_RETRIES} attempts: {last_err}")


def main():
    if not FIRECRAWL_API_KEY:
        raise SystemExit(
            "Missing FIRECRAWL_API_KEY environment variable. "
            "Run: export FIRECRAWL_API_KEY='fc-...'"
        )

    total = sum(len(v) for v in PAGES.values())
    done = 0
    failures = []

    for section, urls in PAGES.items():
        section_dir = os.path.join(OUTPUT_DIR, section)
        os.makedirs(section_dir, exist_ok=True)

        for url, name in urls:
            done += 1
            filename = f"{slugify(name)}.md"
            filepath = os.path.join(section_dir, filename)
            print(f"[{done}/{total}] Scraping {url} -> {filepath}")

            try:
                markdown = scrape_url(url)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"<!-- source: {url} -->\n\n")
                    f.write(markdown)
            except Exception as e:
                print(f"  FAILED: {e}")
                failures.append((url, str(e)))

            time.sleep(REQUEST_DELAY_SECONDS)

    print("\nDone.")
    print(f"  Success: {total - len(failures)}/{total}")
    if failures:
        print("  Failures:")
        for url, err in failures:
            print(f"    - {url}: {err}")


if __name__ == "__main__":
    main()