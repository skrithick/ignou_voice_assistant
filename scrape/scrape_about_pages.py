import os
import re
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

OUTPUT_DIR = "data/about_data"

PAGES = {
    "amenities": "https://www.ignou.ac.in/pages/11",
    "authorities": "https://www.ignou.ac.in/pages/10",
    "awards": "https://www.ignou.ac.in/pages/12",
    "cells_units": "https://www.ignou.ac.in/pages/17",
    "centers_institutes": "https://www.ignou.ac.in/pages/168",
    "chairs": "https://www.ignou.ac.in/pages/14",
    "collaboration": "https://www.ignou.ac.in/pages/15",
    "divisions": "https://www.ignou.ac.in/pages/16",
    "jobs_tenders": "https://www.ignou.ac.in/pages/18",
    "profile": "https://www.ignou.ac.in/pages/20",
    "projects_consultancy": "https://www.ignou.ac.in/pages/21",
    "publications": "https://www.ignou.ac.in/pages/24",
    "recognitions": "https://www.ignou.ac.in/pages/23",
    "regional_centres": "https://www.ignou.ac.in/pages/22",
    "school_of_studies": "https://www.ignou.ac.in/pages/25",
    "study_centres": "https://www.ignou.ac.in/pages/26",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; IGNOU-scraper/1.0)"}

NOISE_TAGS = ["script", "style", "nav", "footer", "header", "noscript"]


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body
    if main is None:
        main = soup

    for a in main.find_all("a"):
        a.replace_with(a.get_text())

    for img in main.find_all("img"):
        img.decompose()

    return str(main)


def scrape_page(name: str, url: str) -> None:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    cleaned_html = clean_html(resp.text)
    markdown_text = md(cleaned_html, heading_style="ATX")
    markdown_text = re.sub(r"\n{3,}", "\n\n", markdown_text).strip()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{name}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {name.replace('_', ' ').title()}\n\nSource: {url}\n\n{markdown_text}")

    print(f"{name}: saved {len(markdown_text)} chars -> {path}")


if __name__ == "__main__":
    for name, url in PAGES.items():
        try:
            scrape_page(name, url)
        except Exception as e:
            print(f"{name}: FAILED ({e})")