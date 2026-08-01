import json
import time
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

domain = "https://www.ignou.ac.in"
qp_url = f"{domain}/studentService/download/questionPapers"
sems = ["June2025", "Dec2025", "Dec2024"]
TARGET_TOTAL = 950

other_languages = {"ORIYA", "ODIA", "HINDI", "URDU", "PUNJABI", "BENGALI", "BANGLA", "TAMIL", "TELUGU", "KANNADA", "MALAYALAM", "MARATHI", "GUJARATI", "ASSAMESE", "NEPALI", "SINDHI", "KASHMIRI", "MANIPURI"}

def english(course_code):
    course_code = course_code.upper()
    for weird in ["_", "-", "(", ")", ","]:
        course_code = course_code.replace(weird, " ")
    words = set(course_code.split())

    return len(words.intersection(other_languages)) == 0

def extract_subject_prefix(course_code):
    prefix = ""
    for character in course_code:
        if character.isalpha():
            prefix += character
        else:
            break
    return prefix.upper() if prefix else "UNKNOWN"

def fetch_papers_from_session(session):
    url = f"{qp_url}/{session}"
    papers = []
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        for row in table.find_all("tr"):
            columns = row.find_all("td")
            if len(columns) >= 4:
                course_code = columns[1].get_text(strip=True)
                link_element = columns[3].find("a", href=True)

                if link_element and english(course_code):
                    full_pdf_url = link_element["href"]
                    if not full_pdf_url.startswith("http"):
                        full_pdf_url = domain + full_pdf_url
                        
                    papers.append({
                        "course_code": course_code,
                        "session": session,
                        "subject_prefix": extract_subject_prefix(course_code),
                        "pdf_url": full_pdf_url
                    })
    except requests.RequestException as error:
        print(f"Error fetching session {session}: {error}")
        
    return papers

def main():
    course_sessions = defaultdict(dict)
    seen_urls = set()

    for sem in sems:
        sem_papers = fetch_papers_from_session(sem)
        for paper in sem_papers:
            if paper["pdf_url"] not in seen_urls:
                seen_urls.add(paper["pdf_url"])
                course_sessions[paper["course_code"]][paper["session"]] = paper
                
        print(f"{sem}: Found {len(sem_papers)} papers.")
        time.sleep(1.0)

    sampled_papers = []
    for sessions_dict in course_sessions.values():
        if len(sessions_dict) == len(sems):
            paper_group = [sessions_dict[s] for s in sems]
            
            if len(sampled_papers) + len(paper_group) > TARGET_TOTAL:
                break
            sampled_papers.extend(paper_group)

    with open("urls.json", "w", encoding="utf-8") as file:
        json.dump(sampled_papers, file, indent=2)
        
    print(f"Saved {len(sampled_papers)}")

if __name__ == "__main__":
    main()