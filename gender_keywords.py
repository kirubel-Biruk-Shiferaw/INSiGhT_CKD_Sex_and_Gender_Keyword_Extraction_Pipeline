"""
Central configuration for sex/gender-related keywords and regex helpers.
English + German lists, plus helper functions to find matches.
"""

import re

# ------------------------------------------------------------
# ENGLISH KEYWORDS
# ------------------------------------------------------------

# complete keyword list (for info / QA)
all_keywords = [
    "male",
    "female",
    "sex",
    "boy",
    "girl",
    "gender",
    "man",
    "men",
    "woman",
    "women",
    "intersex",
    "pregnan",      # stem
    "fertil",       # stem
    "nonbinary",
    "non-binary",
    #"trans ",
    "transsexual",
    "transgender",
    "menopaus",     # stem
    # extended related concepts
    "conception",
    "menstruation",
    "child-bearing",
    "contraception",
    "reproduction",
    "lactation",
]

# regular keywords, no special morphology
keywords = [
    "woman",
    "women",
    "intersex",
    "nonbinary",
    "non-binary",
    "transsexual",
    "transgender",
    "boy",
    "girl",
    "sexes",
    "man,",
    "men.",
    "men,",
]

# stem keywords with different endings: pregnan*, transident*, transition*
keywords_stems = [
    "pregnan",
    #"transition",
    # related stems
    "menstruat",    # menstruation, menstrual, etc.
    "conception",   # conception, conceptual etc.
    "reproduct",    # reproduction, reproductive
]

# keywords with different beginnings and endings (center stems)
# contains also gender plural form
keywords_center_stems = [
    "gender",
    "fertil",
    "menopaus",
    "sexua",
    # related concepts where we only care if they appear anywhere in a word
    "contracept",   # contraception, contraceptive
    "lactat",       # lactation, lactating
    "child-bear",   # child-bearing
    "sex",
]

# keywords with singular/plural form
keywords_singular_plural = [
    "male",
    "female",
    #"sex",
]

# Keywords that need special handling due to high false positive rate
# These will ONLY match as complete words with optional punctuation
strict_boundary_keywords = [
    "man",
    "men",
    #"sex",
    "trans",
]

# Only linebreak-keywords (hyphenated)
# RegEx String: r'\b(%hyphenated_keyword)-\B(?!-)'
hyphenated_keywords = [
    "gen",
    "wom",
    "fe",
    #"non",
    "non-bi",
    "non-bina",
    "preg",
    "pregnan",
    "fer",
    "fertil",
    #"tran",
    #"transi",
    "transg",
    #"trans",
    "transsex",
    "transsexu",
    #"inter",
    "men",
    "meno",
    # extended
    "child-bear",
    "sex",
    "Sex",
]

# RegEx search string for different keyword matching
re_search_strings = {
    # search regular keywords
    "boundaries": r"\b%s\b",
    
    # search strict boundary keywords (allows punctuation after)
    #"strict_boundaries": r"\b(%s)(?=[\s,.\-;:]|\b)", 
    "strict_boundaries": r"\b(%s)(?=[\s,.\-;:/]|$)",
    #"strict_boundaries": r"\b(%s)(?![a-zA-Z])",

    # search stem keywords with different endings
    "stems": r"\b%s\w+",

    # search hyphenated keywords
    "hyphenated": r"\b(%s)-\B(?!-)",

    # search singular/plural keywords
    "singular_plural": r"\b(%s+?)(s\b|es\b|\b)",

    # search keywords with different beginnings and endings
    "center_stems": r"\w*%s\w*",
}

# ------------------------------------------------------------
# GERMAN KEYWORDS (optional, for future)
# ------------------------------------------------------------

all_keywords_de = [
    "gender",
    "gendermedizin",
    "männlich",
    "weiblich",
    "divers",
    "intersex",
    "binär",
    "schwanger",
    "fertil",
    "menopaus",
    "geschlecht",
]

re_search_strings_de = {
    "boundaries": r"\b%s\b",
    "stems": r"\b%s\w+",
    "center_stems": r"\w*%s\w*",
}

keywords_de = [
    "gender",
    "gendermedizin",
    "männlich",
    "weiblich",
    "divers",
]

keywords_stems_de = [
    "intersex",
    "schwanger",
]

keywords_center_stems_de = [
    "binär",
    "fertil",
    "menopaus",
    "geschlecht",
]

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def _compile_pattern(template: str, words):
    """
    Helper: compile a regex from a template and a list of words,
    escaping each word as needed.
    """
    if not words:
        return None
    joined = "|".join(re.escape(w) for w in words)
    pattern = template % joined
    return re.compile(pattern, flags=re.IGNORECASE)


# Precompile EN patterns
BOUNDARY_RE_EN        = _compile_pattern(re_search_strings["boundaries"], keywords)
STRICT_BOUNDARY_RE_EN = _compile_pattern(re_search_strings["strict_boundaries"], strict_boundary_keywords)
STEMS_RE_EN           = _compile_pattern(re_search_strings["stems"], keywords_stems)
CENTER_STEMS_RE_EN    = _compile_pattern(re_search_strings["center_stems"], keywords_center_stems)
SING_PLURAL_RE_EN     = _compile_pattern(re_search_strings["singular_plural"], keywords_singular_plural)
HYPHENATED_RE_EN      = _compile_pattern(re_search_strings["hyphenated"], hyphenated_keywords)

# Optional DE patterns
BOUNDARY_RE_DE        = _compile_pattern(re_search_strings_de["boundaries"], keywords_de)
STEMS_RE_DE           = _compile_pattern(re_search_strings_de["stems"], keywords_stems_de)
CENTER_STEMS_RE_DE    = _compile_pattern(re_search_strings_de["center_stems"], keywords_center_stems_de)


def _flatten_matches(matches):
    """Handle tuples returned by capturing groups (e.g., singular/plural pattern)."""
    flat = []
    for m in matches:
        if isinstance(m, tuple):
            flat.extend([x for x in m if x])
        else:
            flat.append(m)
    return flat


def find_keywords_en(text: str):
    """
    Find all English keyword matches in text using the configured patterns.
    Returns a list of unique, lowercased surface forms.
    """
    text = text or ""
    found = []

    # Regular boundary matches (safe keywords)
    if BOUNDARY_RE_EN:
        found += _flatten_matches(BOUNDARY_RE_EN.findall(text))
    
    # Strict boundary matches (for man, men, sex, trans)
    if STRICT_BOUNDARY_RE_EN:
        found += _flatten_matches(STRICT_BOUNDARY_RE_EN.findall(text))
    
    # Stem matches
    if STEMS_RE_EN:
        found += _flatten_matches(STEMS_RE_EN.findall(text))
    
    # Center stem matches
    if CENTER_STEMS_RE_EN:
        found += _flatten_matches(CENTER_STEMS_RE_EN.findall(text))
    
    # Singular/plural matches
    if SING_PLURAL_RE_EN:
        found += _flatten_matches(SING_PLURAL_RE_EN.findall(text))
    
    # Hyphenated matches
    if HYPHENATED_RE_EN:
        found += _flatten_matches(HYPHENATED_RE_EN.findall(text))

    # Normalize and deduplicate
    found = [m.lower().rstrip('s') if m.lower().endswith('es') or m.lower().endswith('s') else m.lower() 
             for m in found if m]
    
    seen = set()
    unique = []
    for m in found:
        if m not in seen:
            seen.add(m)
            unique.append(m)

    return unique


def find_keywords_de(text: str):
    """
    Find all German keyword matches in text using the configured patterns.
    Returns a sorted list of unique, lowercased surface forms.
    """
    text = text or ""
    found = []

    if BOUNDARY_RE_DE:
        found += _flatten_matches(BOUNDARY_RE_DE.findall(text))
    if STEMS_RE_DE:
        found += _flatten_matches(STEMS_RE_DE.findall(text))
    if CENTER_STEMS_RE_DE:
        found += _flatten_matches(CENTER_STEMS_RE_DE.findall(text))

    found = [m.lower() for m in found if m]
    seen = set()
    uniq = []
    for x in found:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq