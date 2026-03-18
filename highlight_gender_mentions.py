"""
Uses kdigo_gender_mentions.csv produced by extract_gender_mentions.py.
"""
import ast
import re
from pathlib import Path
import fitz
import pandas as pd

# Import the same keyword detection logic
from gender_keywords import find_keywords_en

PDF_IN  = "KDIGO-2024-CKD-Guideline.pdf"
CSV_IN  = "kdigo_gender_mentions.csv"
PDF_OUT = "KDIGO-2024-CKD-Guideline_highlighted_wordsafe.pdf"

def parse_terms(x):
    """Parse matched_terms column which may be a stringified Python list."""
    if isinstance(x, list):
        return x
    if isinstance(x, str) and x.strip():
        try:
            v = ast.literal_eval(x)
            if isinstance(v, list):
                return v
        except Exception:
            pass
        # fallback: comma-separated
        return [t.strip() for t in x.split(",") if t.strip()]
    return []


def is_valid_match(word_text, term):
    """
    Check if word_text is a valid match for term.
    Uses similar logic as gender_keywords.py to avoid false positives.
    """
    # raw lowercase (keep hyphen info)
    raw_lower = word_text.lower()
    # stripped of punctuation / hyphen for safety comparisons
    word_lower = raw_lower.strip('.,;:!?()[]{}"\'-')
    term_lower = term.lower()

    SENSITIVE_WORDS = {'man', 'men', 'sex', 'trans'}

    # --- Special handling for 'sex' ---
    if term_lower == 'sex':
        # Accept:
        #   - exact 'sex'
        #   - hyphenated 'sex-' forms like 'sex-specific', 'sex-based'
        if word_lower == 'sex' or raw_lower.startswith('sex-'):
            return True
        return False

    # --- Strict handling for other sensitive short words ---
    if term_lower in {'man', 'men'}:
        # Must be exact 'man'/'men' (or plural) after stripping punctuation
        return word_lower == term_lower or word_lower == term_lower + 's'

    if term_lower == 'trans':
        # Allow 'trans' as word, but not substrings (e.g., 'transport')
        if word_lower == 'trans':
            return True
        # let other patterns (like 'transgender') be handled via other terms
        return False

    # --- For stems (like 'pregnan', 'fertil', etc.), allow prefix matches ---
    if len(term_lower) <= 8 and not term_lower.endswith('s'):
        # e.g., 'pregnan' -> 'pregnant', 'fertil' -> 'fertility'
        return word_lower.startswith(term_lower)

    # --- Default: exact or plural match ---
    return word_lower == term_lower or word_lower == term_lower + 's'


def highlight_with_validation(page, terms, color=(1, 1, 0)):
    """
    Highlight terms using word-level bounding boxes with validation.
    Re-validates each match to avoid false positives like 'men' in 'management'.
    """
    count = 0
    # get_text("words") returns: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
    words = page.get_text("words")
    
    for x0, y0, x1, y1, wtext, *_ in words:
        # Check if this word is a valid match for any of our terms
        for term in terms:
            if is_valid_match(wtext, term):
                rect = fitz.Rect(x0, y0, x1, y1)
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=color)
                annot.update()
                count += 1
                break  # Only highlight once per word
    
    return count


def highlight_phrases(page, phrases, color=(1, 1, 0)):
    """
    Highlight multi-word phrases or hyphenated terms.
    """
    count = 0
    for phrase in phrases:
        try:
            rects = page.search_for(phrase, flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES)
            for rect in rects:
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=color)
                annot.update()
                count += 1
        except Exception as e:
            print(f"Warning: Could not highlight phrase '{phrase}': {e}")
    
    return count


def main():
    df = pd.read_csv(CSV_IN)
    df["page"] = pd.to_numeric(df["page"], errors="coerce").astype(int)
    df["matched_terms"] = df["matched_terms"].apply(parse_terms)
    
    pdf_path = Path(PDF_IN)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {PDF_IN}")
    
    doc = fitz.open(PDF_IN)
    total = 0
    
    print("🔍 Analyzing extracted terms...")
    all_terms = set()
    for _, row in df.iterrows():
        all_terms.update(row["matched_terms"])
    print(f"📊 Unique terms to highlight: {sorted(all_terms)}")
    
    for page_index in range(len(doc)):
        page_num = page_index + 1
        page = doc[page_index]
        
        page_rows = df[df["page"] == page_num]
        if page_rows.empty:
            continue
        
        # Collect all terms for this page
        terms = set()
        for _, row in page_rows.iterrows():
            for term in row["matched_terms"]:
                if isinstance(term, str) and term.strip():
                    terms.add(term.strip())
        
        if not terms:
            continue
        
        print(f"📄 Page {page_num}: Processing {len(terms)} terms...")
        
        # IMPORTANT: Re-extract keywords from the actual page text
        # This ensures we only highlight what would actually match our patterns
        page_text = page.get_text()
        valid_terms_on_page = set(find_keywords_en(page_text))
        
        # Only highlight terms that are both in our CSV AND re-validated on the page
        terms_to_highlight = terms.intersection(valid_terms_on_page)
        
        if not terms_to_highlight:
            print(f"  ⚠️  No valid terms after re-validation")
            continue
        
        print(f"  ✓ Highlighting: {terms_to_highlight}")
        
        # Separate into words and phrases
        words = set()
        phrases = set()
        
        for t in terms_to_highlight:
            if " " in t or t.count("-") > 1:  # Multi-word or complex hyphenation
                phrases.add(t)
            else:
                words.add(t)
        
        # Highlight single words with validation
        if words:
            count = highlight_with_validation(page, words)
            total += count
            print(f"  → {count} word highlights")
        
        # Highlight phrases
        if phrases:
            count = highlight_phrases(page, phrases)
            total += count
            print(f"  → {count} phrase highlights")
    
    doc.save(PDF_OUT, deflate=True)
    doc.close()
    
    print(f"\n✅ Highlighting complete: {total} annotations added.")
    print(f"💾 Saved as: {PDF_OUT}")


if __name__ == "__main__":
    main()