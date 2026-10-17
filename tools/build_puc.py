"""Build Karnataka 2nd PUC entries (official dpue-exam.karnataka.gov.in PDFs).

Links are collected from a public index page that lists the official DPUE/KSEAB PDFs by
exam. The PDFs themselves are served by the Karnataka government (dpue-exam.karnataka.gov.in).
"""
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

INDEX_PAGE = "https://www.jagranjosh.com/articles/karnataka-2nd-puc-previous-year-question-papers-pdf-download-1800004529-1"
OFFICIAL = "https://kseab.karnataka.gov.in/"
OUT = Path(__file__).resolve().parent.parent / "data" / "sources" / "puc.json"

SUBJECTS = {
    "01": "Kannada", "02": "English", "03": "Hindi", "04": "Tamil", "05": "Telugu", "06": "Malayalam",
    "07": "Marathi", "08": "Urdu", "09": "Sanskrit", "11": "Arabic", "12": "French",
    "16": "Optional Kannada", "21": "History", "22": "Economics", "23": "Logic", "24": "Geography",
    "26": "Hindustani Music", "27": "Business Studies", "28": "Sociology", "29": "Political Science",
    "30": "Accountancy", "31": "Statistics", "32": "Psychology", "33": "Physics", "34": "Chemistry",
    "35": "Mathematics", "36": "Biology", "37": "Geology", "40": "Electronics", "41": "Computer Science",
    "52": "Education", "61": "Information Technology", "62": "Retail", "63": "Automobile",
    "64": "Health Care", "65": "Beauty & Wellness", "67": "Home Science", "75": "Basic Mathematics",
}
LANGUAGES = {"01", "02", "03", "04", "05", "06", "07", "08", "09", "11", "12"}
STREAMS = {
    "Science": {"33", "34", "35", "36", "37", "40", "41", "31", "67"},
    "Commerce": {"30", "27", "22", "31", "75", "41", "62", "61"},
    "Arts": {"21", "22", "23", "24", "26", "28", "29", "32", "52", "16", "37", "67", "31", "75"},
    "Vocational": {"61", "62", "63", "64", "65"},
}
EXAMS = {"1": "Exam 1 (March)", "2": "Exam 2 (April-May)", "3": "Exam 3 (June)"}


def main():
    req = urllib.request.Request(INDEX_PAGE, headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "ignore")
    entries, seen = [], set()
    year = exam = None
    pattern = r'<(?:h[2-4]|p|strong|td)[^>]*>\s*((?:<[^>]+>\s*)*20\d\d\s*-?\s*Exam\s*\d[^<]{0,20})<|<a [^>]*href="(https://dpue-exam\.karnataka\.gov\.in[^"]+)"[^>]*>(.*?)</a>'
    for m in re.finditer(pattern, page, re.S):
        if m.group(1):
            head = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
            hm = re.search(r"(20\d\d)\s*-?\s*Exam\s*(\d)", head, re.I)
            if hm:
                year, exam = hm.group(1), hm.group(2)
            continue
        if not year:
            continue
        url = html.unescape(m.group(2)).strip()
        label = html.unescape(re.sub(r"<[^>]+>", "", m.group(3))).strip()
        cm = re.search(r"(\d{2})", label)
        if not cm or cm.group(1) not in SUBJECTS:
            continue
        code = cm.group(1)
        fname = urllib.parse.unquote(url.rsplit("/", 1)[1])
        fcodes = re.findall(r"(?<!\d)(\d{2})(?!\d)", fname.replace("2024", "").replace("2025", ""))
        if fcodes and code not in fcodes:
            continue  # index page links the wrong file for this subject
        if url in seen:
            continue  # index page reuses another exam's file
        seen.add(url)
        scheme = " (Old Scheme)" if "OS" in label.upper() or "OLD" in label.upper() else ""
        subject = f"{SUBJECTS[code]}{scheme} ({code})"
        streams = ["Languages"] if code in LANGUAGES else [s for s, codes in STREAMS.items() if code in codes]
        for stream in streams:
            entries.append({
                "board": "Karnataka 2nd PUC",
                "course": "2nd PUC (12th)",
                "stream": stream,
                "group": year,
                "semester": EXAMS.get(exam, f"Exam {exam}"),
                "subject": subject,
                "code": code,
                "year": year,
                "type": "Previous Year Question Paper",
                "url": url.replace(" ", "%20"),
                "source": OFFICIAL,
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(entries, indent=1, ensure_ascii=False))
    print(f"wrote {len(entries)} PUC entries ({len(seen)} PDFs) to {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
