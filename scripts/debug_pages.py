from pypdf import PdfReader
reader = PdfReader('Paper/main.pdf')

with open('Paper/main.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if 'enlargethispage' in line and idx >= 1040:
        prev_idx = idx - 2
        while prev_idx >= 0 and not lines[prev_idx].strip():
            prev_idx -= 1
        prev_txt = lines[prev_idx].strip()
        matching_pages = []
        for p_idx, page in enumerate(reader.pages, 1):
            if prev_txt[:30].lower() in page.extract_text().lower():
                matching_pages.append(p_idx)
        print(f'Line {idx:4d} ({line.strip()}): after "{prev_txt[:30]}" -> Page {matching_pages}')
