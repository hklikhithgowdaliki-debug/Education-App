"""Build VTU engineering entries from the official VTU model-question-paper page."""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

SOURCE_PAGE = "https://vtu.ac.in/model-question-paper-b-e-b-tech-b-arch/"
OUT = Path(__file__).resolve().parent.parent / "data" / "sources" / "vtu.json"

BRANCHES = {
    "CS": "Computer Science", "IS": "Information Science", "AI": "AI & ML",
    "AD": "AI & Data Science", "CD": "Computer Science (Data Science)",
    "CY": "Computer Science (Cyber Security)", "CB": "Computer Science & Business Systems",
    "IC": "Computer Science (IoT & Cyber Security)", "CG": "Computer Science (Design)",
    "EC": "Electronics & Communication", "EE": "Electrical & Electronics",
    "EI": "Electronics & Instrumentation", "TE": "Electronics & Telecommunication",
    "TC": "Electronics & Telecommunication", "ET": "Electronics & Telecommunication",
    "VL": "Electronics (VLSI)", "ML": "Medical Electronics", "BM": "Biomedical Engineering",
    "ME": "Mechanical", "AU": "Automobile", "IP": "Industrial & Production",
    "IM": "Industrial Engineering & Management", "MA": "Marine Engineering",
    "AE": "Aeronautical", "AS": "Aerospace", "RA": "Robotics & Automation",
    "MR": "Mechatronics", "MT": "Mechatronics", "CV": "Civil", "CT": "Construction Technology",
    "EV": "Environmental", "CH": "Chemical", "BT": "Biotechnology", "PT": "Polymer Science",
    "SS": "Silk Technology", "TX": "Textile Technology", "MN": "Mining", "CR": "Ceramics",
    "AR": "Architecture", "ARC": "Architecture", "RI": "Robotics & AI", "AG": "Agricultural Engineering",
    "UE": "Electronics (Instrumentation)", "MM": "Metallurgy & Materials", "ST": "Ship Technology",
    "SA": "Space & Aeronautics", "DS": "Computer Science (Data Science)", "CO": "Computer & Communication",
    "XX": "Common Electives (All Branches)", "BOK": "Common Subjects", "UHV": "Common Subjects",
    "RM": "Common Subjects", "PE": "Common Subjects", "CM": "Computer Science (Mobile)",
}
FIRST_YEAR = "First Year (Common)"


def scheme_and_sem(title):
    t = title.upper()
    scheme = None
    m = re.search(r"(20\d\d)\s*\(?\s*SCHEME", t) or re.search(r"SCHEME\s*\(?\s*(20\d\d)", t) \
        or re.search(r"(20\d\d)\s*SCHEME", t) or re.search(r"\((?:CBCS\s*)?(20\d\d)", t) \
        or re.search(r"(20\d\d)", t)
    if m:
        scheme = m.group(1)
    sem = None
    m = re.search(r"(\d)(?:ST|ND|RD|TH)?\s*(?:&|AND)\s*(\d)(?:ST|ND|RD|TH)?\s*SEM", t)
    if m:
        sem = f"{m.group(1)}&{m.group(2)}"
    else:
        m = re.search(r"(\d)\s*(?:ST|ND|RD|TH)?\s*SEM", t) or re.search(r"SEMESTER\s*(\d)", t)
        if m:
            sem = m.group(1)
        else:
            roman = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6", "VII": "7", "VIII": "8"}
            m = re.search(r"\b(VIII|VII|VI|IV|V|III|II|I)\s+SEM", t)
            if m:
                sem = roman[m.group(1)]
            elif "THIRD / FOURTH" in t:
                sem = "3&4"
    return scheme, sem


def branch_for(code, sem):
    c = code.upper()
    if sem in ("1", "2", "1&2") or re.match(r"^\d?B?(MAT|PHY|CHE|ENG|CED|BEE|SKS|PSP|ESC|ETC|PLC|KSK|KBK|ICO|SFH|IDT|EME|ELN|CIV|BE|BEC|BPL|BI)", c):
        return FIRST_YEAR
    m = re.match(r"^\d{0,2}([A-Z]+)", c)
    raw = m.group(1) if m else ""
    candidates = [raw[1:], raw] if raw.startswith("B") and re.match(r"^\d{0,2}B", c) and not c[:2].isdigit() else [raw]
    for letters in candidates:
        for k in sorted(BRANCHES, key=len, reverse=True):
            if letters.startswith(k):
                return BRANCHES[k]
    if letters.startswith("MAT") or letters.startswith("MA"):
        return "Mathematics (All Branches)"
    return "Other / Common Subjects"


def main():
    req = urllib.request.Request(SOURCE_PAGE, headers={"User-Agent": "Mozilla/5.0 EduPapersCatalogBot"})
    page = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "ignore")
    sections = re.split(r'<div class="col-md-12 mqtitle\d*">', page)[1:]
    entries, seen = [], set()
    for sec in sections:
        title = html.unescape(re.sub(r"<[^>]+>", "", sec.split("</div>", 1)[0])).strip()
        body = sec.split("mqtitle", 1)[0]
        program = "B.E./B.Tech"
        tu = title.upper()
        if "MBA" in tu:
            continue
        if "B.ARCH" in tu and "B.E" not in tu:
            program = "B.Arch"
        if "B.SC" in tu:
            continue
        scheme, sem = scheme_and_sem(title)
        rows = re.split(r'<div class="row zcol-pay">', body)[1:]
        for row in rows:
            content = re.search(r'zpay-content">(.*?)</div>', row, re.S)
            name = html.unescape(re.sub(r"<[^>]+>", "", content.group(1))) if content else ""
            name = " ".join(re.split(r"(?i)updated\s*date", name)[0].split())
            for url, label in re.findall(r'href="(https://vtu\.ac\.in/pdf/QP/[^"]+\.pdf)"[^>]*>.*?<br\s*/?>\s*([^<]+)</a>', row, re.S | re.I):
                label = " ".join(html.unescape(label).split())
                key = (url, scheme, sem)
                if key in seen:
                    continue
                seen.add(key)
                file_code = re.sub(r"(?i)(set\d|qp\d|_.*)$", "", url.rsplit("/", 1)[1][:-4])
                code_like = re.match(r"^\d{0,2}[A-Za-z]{2,}\d", label)
                code = label.split("/")[0].strip() if code_like else file_code
                subject = name or label
                if name and not code_like:
                    subject = f"{name} ({label})"
                elif name:
                    subject = f"{name} - {label}"
                branch = "Architecture" if program == "B.Arch" else branch_for(code, sem)
                named = next((v for v in set(BRANCHES.values()) if name.lower().startswith(v.lower())), None)
                if named and branch.startswith("Other"):
                    branch = named
                elif branch.startswith("Other") and " - " in subject:
                    branch = name.split(" - ")[0] if name else branch
                subject = re.sub(r"\((?:Download\s*)?\)$", "", subject.replace("(Download Paper-", "(Paper ")).strip()
                entries.append({
                    "board": "VTU Engineering",
                    "course": program,
                    "stream": branch,
                    "group": f"{scheme} Scheme" if scheme else "Older Schemes",
                    "semester": f"Sem {sem}" if sem else "All Semesters",
                    "subject": subject,
                    "code": code.upper(),
                    "year": scheme or "",
                    "type": "Model Question Paper",
                    "url": url,
                    "source": SOURCE_PAGE,
                })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(entries, indent=1, ensure_ascii=False))
    print(f"wrote {len(entries)} VTU entries to {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
