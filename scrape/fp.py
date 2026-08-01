from make_meta import get_first_page_text

text = get_first_page_text("data/qp_pdfs/ACS-01_Dec2024.pdf")
print(repr(text))
print("---")
print(text)