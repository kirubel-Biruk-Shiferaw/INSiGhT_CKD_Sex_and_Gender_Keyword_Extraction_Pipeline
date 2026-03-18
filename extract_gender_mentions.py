"""
extract_gender_mentions.py

Extract sex/gender-related mentions from KDIGO 2024 CKD guideline
using detailed keyword lists and regex patterns from gender_keywords.py.
"""
# python -m spacy download en_core_web_lg, make sure to download this spacy model

import csv
import json
from pathlib import Path

import fitz
import spacy
from tqdm import tqdm

from gender_keywords import find_keywords_en  # (and find_keywords_de for the german guidelines)

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------
PDF_PATH = "guideline.pdf"
OUT_CSV  = "guideline_gender_mentions.csv"
OUT_JSON = "guideline_gender_mentions.jsonl"

# Section page mapping (explicit from user)
SECTION_MAP = [
    (1, 19, "Overview"),
    (20, 25, "Introduction & Key Concepts"),
    (26, 28, "Special Considerations"),
    (29, 33, "Relative & Absolute Risk"),
    (34, 53, "Summary of Recommendation Statements"),
    (54, 80, "Evaluation of CKD"),
    (81, 89, "Risk Assessment in CKD"),
    (90, 130, "Delaying CKD Progression / Managing Complications"),
    (131, 139, "Medication Management & Drug Stewardship"),
    (140, 154, "Optimal Models of Care"),
    (155, 158, "Research Recommendations"),
    (159, 167, "Methods of Guideline Development"),
    (168, 179, "Biography & Acknowledgments"),
    (180, 199, "References"),
]


def get_section(page_num: int) -> str:
    for start, end, label in SECTION_MAP:
        if start <= page_num <= end:
            return label
    return "Unknown"


# ------------------------------------------------------------
# 2. NLP SETUP
# ------------------------------------------------------------
nlp = spacy.load("en_core_web_lg", disable=["ner", "tagger", "lemmatizer"])
nlp.max_length = 5_000_000


def normalize_text(text: str) -> str:
    """Fix common ligatures and hyphen variants."""
    subs = {
        "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
        "\u00AD": "",  # soft hyphen
        "\u2010": "-", "\u2011": "-", "\u2012": "-",
        "\u2013": "-", "\u2014": "-",
    }
    for k, v in subs.items():
        text = text.replace(k, v)
    return text


def extract_pages(pdf_path):
    """Yield (page_num, normalized_text) tuples."""
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            text = normalize_text(page.get_text("text"))
            yield i, text


# ------------------------------------------------------------
# 3. MAIN EXTRACTION LOOP
# ------------------------------------------------------------
def main():
    rows = []

    for page_num, text in tqdm(list(extract_pages(PDF_PATH)), desc="Processing KDIGO pages"):
        if not text.strip():
            continue

        section = get_section(page_num)
        doc = nlp(text)
        sents = list(doc.sents)

        for i, sent in enumerate(sents):
            stext = sent.text.strip()
            if not stext:
                continue

            # Find keyword matches in this sentence using our detailed lists
            matches_en = find_keywords_en(stext)
            # If you ever want DE detection, you could also run:
            # matches_de = find_keywords_de(stext)
            # matches = sorted(set(matches_en + matches_de))
            matches = matches_en

            if matches:
                # Grab ±2 sentences as context
                start_i = max(0, i - 1)
                end_i = min(len(sents), i + 2)
                context = " ".join(s.text.strip() for s in sents[start_i:end_i])

                rows.append({
                    "page": page_num,
                    "section": section,
                    "sentence": stext,
                    "context": context,
                    "matched_terms": matches,
                })

    # --------------------------------------------------------
    # 4. SAVE OUTPUTS
    # --------------------------------------------------------
    out_path = Path(OUT_CSV)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["page", "section", "sentence", "context", "matched_terms"],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Extracted {len(rows)} sentences with keyword matches.")
    print(f"💾 Saved CSV:   {OUT_CSV}")
    print(f"💾 Saved JSONL: {OUT_JSON}")


if __name__ == "__main__":
    main()
