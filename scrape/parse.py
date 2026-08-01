import json
import os
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv()

PDF_DIR, MD_DIR = "data/qp_pdfs", "data/qp_md"
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(MD_DIR, exist_ok=True)

app = Firecrawl(api_key=os.environ.get("FIRECRAWL_API_KEY"))


def get_filename(paper, ext):
    safe_code = paper["course_code"].replace(" ", "").replace("/", "-")
    return f"{safe_code}_{paper['session']}.{ext}"


def download_pdf(paper):
    save_path = os.path.join(PDF_DIR, get_filename(paper, "pdf"))
    if os.path.exists(save_path):
        return
    response = requests.get(paper["pdf_url"], stream=True, timeout=15)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        f.writelines(response.iter_content(chunk_size=8192))


def scrape_paper(paper):
    save_path = os.path.join(MD_DIR, get_filename(paper, "md"))
    result = app.scrape(paper["pdf_url"], formats=["markdown"])
    if result.markdown:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(result.markdown)
        return True
    return False


def main():
    with open("urls.json", "r", encoding="utf-8") as f:
        papers = json.load(f)
    print(f"Loaded {len(papers)} papers.")

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(download_pdf, papers)
    print("PDF downloads complete.")

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(scrape_paper, papers))

    print(f"Saved {sum(results)}/{len(papers)} Markdown files successfully.")


if __name__ == "__main__":
    main()