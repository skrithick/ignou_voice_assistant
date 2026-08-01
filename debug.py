import os
from collections import Counter
from scrape.make_meta import get_first_page_text, extract_metadata_regex, CODE_RE, SESSION_TOKENS

PDF_DIR = "data/qp_pdfs"

reasons = Counter()
examples = {}

for filename in sorted(os.listdir(PDF_DIR)):
    if not filename.endswith(".pdf"):
        continue

    path = os.path.join(PDF_DIR, filename)
    text = get_first_page_text(path)

    if extract_metadata_regex(text) is not None:
        continue

    if not text.strip():
        reason = "empty_text (Hindi page or extraction failed)"
    elif not CODE_RE.search(text):
        reason = "no_code_match"
    else:
        clean = text.lower().replace(" ", "").replace(",", "")
        if not any(token in clean for token in SESSION_TOKENS):
            reason = "no_session_match"
        else:
            reason = "no_name_match"

    reasons[reason] += 1
    examples.setdefault(reason, []).append(filename)

print("Skip reason breakdown:")
for reason, count in reasons.most_common():
    print(f"  {reason}: {count}")
    for f in examples[reason][:3]:
        print(f"    e.g. {f}")