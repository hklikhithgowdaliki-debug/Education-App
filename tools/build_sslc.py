"""Build Karnataka SSLC (Class 10) entries from the karnatakaboard.com paper index.

Official KSEAB pages (kseab.karnataka.gov.in) are the primary publisher; this index mirrors
the KSEAB question papers by subject, medium, set and exam session as direct PDF links.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

INDEX_PAGE = "https://www.karnatakaboard.com/"
OUT = Path(__file__).resolve().parent.parent / "data" / "sources" / "sslc.json"
MONTHS = {"mar": "Mar", "pr": "Apr", "apr": "Apr", "may": "May", "jun": "Jun", "jul": "Jul",
          "aug": "Aug", "sep": "Sep", "oct": "Oct"}
SESSION = {"Mar": "Exam 1 (Main)", "Apr": "Exam 1 (Main)", "May": "Exam 1 (Main)",
           "Jun": "Exam 2 (Supplementary)", "Jul": "Exam 2 (Supplementary)",
           "Aug": "Exam 3 (Supplementary)", "Sep": "Exam 3 (Supplementary)", "Oct": "Exam 3 (Supplementary)"}
MEDIUMS = {"e": "English", "k": "Kannada", "u": "Urdu", "m": "Marathi", "t": "Tamil", "te": "Telugu",
           "h": "Hindi", "ek": "English/Kannada"}


def subject_group(name):
    n = name.lower()
    if "language" in n or n.split()[0] in {"kannada", "english", "hindi", "urdu", "sanskrit", "tamil",
                                          "telugu", "marathi", "arabic", "persian", "konkani", "tulu", "malayalam"}:
        return "Languages"
    for key, label in (("mathematics", "Mathematics"), ("social", "Social Science"), ("science", "Science")):
        if key in n:
            return label
    return "Vocational & Other Subjects"


def main():
    req = urllib.request.Request(INDEX_PAGE, headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "ignore")
    slugs = sorted(set(re.findall(r'https://www\.karnatakaboard\.com/papers/(class-10-[a-z0-9-]+)\.html', page)))
    entries = []
    for slug in slugs:
        toks = slug.split("-")[2:]
        if not toks or not re.fullmatch(r"20\d\d", toks[-1]):
            continue
        year = toks.pop()
        month = MONTHS.get(toks[-1], "") if toks else ""
        if month:
            toks.pop()
        model = "model" in toks
        flags = {t for t in toks if t in {"supp", "cce", "rf", "rr", "pf", "nsqf", "model", "paper", "pr"}}
        set_ = paper_no = version = None
        words, code, med = [], None, ""
        i = 0
        while i < len(toks):
            t = toks[i]
            if t == "set" and i + 1 < len(toks):
                set_ = toks[i + 1].upper(); i += 2
                if i < len(toks) and toks[i].isdigit() and len(toks[i]) == 1:
                    set_ += f"-{toks[i]}"; i += 1
                continue
            if re.fullmatch(r"v\d", t):
                version = t[1]; i += 1; continue
            if t in ("paper", "p") and i + 1 < len(toks) and toks[i + 1].isdigit():
                paper_no = toks[i + 1]; i += 2; continue
            if re.fullmatch(r"p\d", t):
                paper_no = t[1]; i += 1; continue
            m = re.fullmatch(r"(\d{2})([a-z]{0,3})", t)
            if m and code is None and words:
                code, med = m.group(1), m.group(2)
                if not med and i + 1 < len(toks) and (toks[i + 1] in MEDIUMS or (
                        re.fullmatch(r"[a-z]{1,2}", toks[i + 1]) and toks[i + 1] not in flags | {"p", "pr"})):
                    med = toks[i + 1]; i += 1
                i += 1; continue
            if code is None and t not in flags and not re.fullmatch(r"p\d", t):
                words.append(t)
            i += 1
        if code is None or not words:
            continue
        if med.startswith("h") and len(med) > 1:
            med = med[1:]
        prep = words[0] in ("preparatory", "mqp")
        words = [w for w in words if w not in ("preparatory", "mqp", "class", "theory")]
        if len(words) >= 3 and words[1] == "language" and words[0] in ("first", "second", "third"):
            words = words[2:] + words[:2]
        words = ["telugu" if w == "telu" else "apparel" if w == "apparels" else w for w in words]
        subject = " ".join(w if w in {"and", "of"} else w.capitalize() for w in words)
        subject = re.sub(r"\s+\d$", "", subject).replace("Carnatic Music Hindustani Music", "Carnatic / Hindustani Music")
        model = model or prep
        medium = MEDIUMS.get(med, med.upper())
        variant = ("Regular Fresher" if "rf" in flags else "Regular Repeater" if "rr" in flags
                   else "Private Fresher" if "pf" in flags else "Private Repeater" if "pr" in flags else "")
        if "rr" in flags and "pr" in flags:
            variant = "Repeater (Regular & Private)"
        if version:
            variant = f"{variant}, Version {version}".lstrip(", ")
        bits = [f"Set {set_}" if set_ else "", f"Paper {paper_no}" if paper_no else "",
                f"{medium} medium" if medium else "", variant]
        detail = ", ".join(b for b in bits if b)
        if model:
            session = "Model Question Papers"
        elif year == "2021":
            session = "Exam 2021 (Special)"
        else:
            session = SESSION.get(month, "Annual Exam")
            if "supp" in flags and session.startswith("Exam 1"):
                session = "Exam 2 (Supplementary)"
        entries.append({
            "board": "Karnataka SSLC",
            "course": "SSLC (10th)",
            "stream": subject_group(subject),
            "group": year,
            "semester": session,
            "subject": f"{subject} ({code}{med.upper()})" + (f" - {detail}" if detail else ""),
            "code": f"{code}{med.upper()}",
            "year": year,
            "type": ("Model Question Paper" if model else "Previous Year Question Paper")
                    + (f" - {month} {year}" if month else ""),
            "url": f"https://www.karnatakaboard.com/papers/{slug}.pdf",
            "source": "https://kseab.karnataka.gov.in/ (via karnatakaboard.com)",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(entries, indent=1, ensure_ascii=False))
    print(f"wrote {len(entries)} SSLC entries of {len(slugs)} links to {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
