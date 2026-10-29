#!/usr/bin/env python3
"""Shared text utilities for seo-mentor keyword analyzers.

Pure standard library on purpose: the analyzers must run on a bare Python 3
install without BeautifulSoup, network access, or an ML runtime.

The scoring helpers are heuristic models, not a reimplementation of Google's
ranking system. See references/keyword_dilution_model.md for the caveats.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional, Sequence

CJK_RANGES = (
    "\u3400-\u4dbf"  # CJK Extension A
    "\u4e00-\u9fff"  # CJK Unified Ideographs
    "\uf900-\ufaff"  # CJK Compatibility Ideographs
    "\u3040-\u30ff"  # Hiragana / Katakana
    "\uac00-\ud7af"  # Hangul syllables
)
CJK_CHAR_RE = re.compile(f"[{CJK_RANGES}]")
WORD_RE = re.compile(r"[a-z0-9]+")
LETTER_RUN_RE = re.compile(r"[^\W_]+", re.UNICODE)
SCRIPT_RUN_RE = re.compile(f"([a-z0-9]+)|([{CJK_RANGES}]+)")

SKIP_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "template",
    "iframe",
    "canvas",
    "object",
    "embed",
}
MAIN_TAGS = {"main", "article"}


def normalize_text(text: Optional[str]) -> str:
    """Fold Latin diacritics and case while keeping CJK text tokenizable.

    NFKD alone would decompose Hangul syllables into conjoining Jamo and kana
    with dakuten into base + combining mark, which breaks tokenization and word
    counts. Strip only the Latin combining block, then NFC recomposes Hangul and
    kana back into their precomposed forms.
    """
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(
        ch for ch in decomposed if not "\u0300" <= ch <= "\u036f"
    )
    return unicodedata.normalize("NFC", stripped).casefold()


def tokenize(text: Optional[str]) -> List[str]:
    """Split text into ASCII words plus CJK unigrams and bigrams.

    Bigrams keep phrase matching meaningful for languages without spaces while
    unigrams keep single-character recall. Punctuation and parentheses are
    dropped, so ``(TTS)`` normalizes to the token ``tts``.
    """
    normalized = normalize_text(text)
    tokens: List[str] = []
    for ascii_run, cjk_run in SCRIPT_RUN_RE.findall(normalized):
        if ascii_run:
            tokens.append(ascii_run)
        elif cjk_run:
            chars = list(cjk_run)
            tokens.extend(chars)
            tokens.extend(chars[i] + chars[i + 1] for i in range(len(chars) - 1))
    return tokens


def count_words(text: Optional[str]) -> int:
    """Script-aware word count.

    CJK runs count as one per character because those languages are not space
    delimited; every other script counts one per whitespace-delimited run. This
    keeps Arabic, Cyrillic and Korean pages from being misread as thin content.
    """
    normalized = normalize_text(text)
    total = 0
    for run in LETTER_RUN_RE.findall(normalized):
        cjk_chars = len(CJK_CHAR_RE.findall(run))
        total += cjk_chars + (1 if len(run) > cjk_chars else 0)
    return total


def collapse(text: str) -> str:
    return " ".join(text.split())


@dataclass
class PageText:
    title: str = ""
    h1: str = ""
    meta_description: str = ""
    body: str = ""
    first_paragraph: str = ""
    word_count: int = 0
    h1_count: int = 0
    title_count: int = 0


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.main_depth = 0
        self.paragraph_depth = 0
        self.title_parts: List[str] = []
        self.h1_parts: List[str] = []
        self.body_parts: List[str] = []
        self.main_parts: List[str] = []
        self.first_paragraph = ""
        self._paragraph_parts: List[str] = []
        self.meta_description = ""
        self.h1_count = 0
        self.title_count = 0
        self._in_title = False
        self._in_h1 = False
        self._h1_done = False

    # -- parser hooks -----------------------------------------------------
    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        attributes = {str(k).lower(): (v or "") for k, v in attrs}
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if tag in MAIN_TAGS:
            self.main_depth += 1
        if tag == "title":
            self.title_count += 1
            self._in_title = True
        elif tag == "h1":
            self.h1_count += 1
            self._in_h1 = True
        elif tag == "meta":
            name = attributes.get("name", "").lower()
            if name == "description" and attributes.get("content") and not self.meta_description:
                self.meta_description = attributes["content"]
        elif tag == "p":
            self.paragraph_depth += 1
            if self.paragraph_depth == 1:
                self._paragraph_parts = []

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            if self.skip_depth:
                self.skip_depth -= 1
            return
        if tag in MAIN_TAGS:
            if self.main_depth:
                self.main_depth -= 1
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
            if self.h1_parts:
                self._h1_done = True
        elif tag == "p":
            if self.paragraph_depth:
                self.paragraph_depth -= 1
                if self.paragraph_depth == 0 and not self.first_paragraph:
                    candidate = collapse(" ".join(self._paragraph_parts))
                    if len(candidate) >= 20:
                        self.first_paragraph = candidate
                self._paragraph_parts = []

    def handle_data(self, data: str) -> None:
        if self.skip_depth or not data.strip():
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        if self._in_h1:
            if not self._h1_done:
                self.h1_parts.append(data)
            return
        self.body_parts.append(data)
        if self.main_depth:
            self.main_parts.append(data)
        if self.paragraph_depth:
            self._paragraph_parts.append(data)


def extract_page(html: str) -> PageText:
    """Extract title, H1, meta description and main body text from raw HTML."""
    parser = _PageParser()
    try:
        parser.feed(html or "")
        parser.close()
    except Exception:  # malformed markup should never crash an audit
        pass

    body = collapse(" ".join(parser.main_parts))
    if count_words(body) < 30:
        body = collapse(" ".join(parser.body_parts))
    if not body:
        body = collapse(" ".join(parser.main_parts or parser.body_parts))

    title = collapse(" ".join(parser.title_parts))
    h1 = collapse(" ".join(parser.h1_parts))
    return PageText(
        title=title,
        h1=h1,
        meta_description=collapse(parser.meta_description),
        body=body,
        first_paragraph=parser.first_paragraph,
        word_count=count_words(body),
        h1_count=parser.h1_count,
        title_count=parser.title_count,
    )


@dataclass
class FieldScore:
    tokens: int
    coverage: float
    length_penalty: float
    bm25: float


def bm25_field(
    field_tokens: Sequence[str],
    query_tokens: Sequence[str],
    k1: float = 1.2,
    b: float = 0.75,
    avgdl: Optional[float] = None,
    idf: Optional[Dict[str, float]] = None,
) -> FieldScore:
    """BM25 score for one query against one field, normalized to 0..1.

    ``coverage`` is the achieved BM25 divided by the best achievable score for
    the same query (tf=1 in a field of exactly ``avgdl`` tokens). Values above
    one are clamped, so repeated keywords cannot inflate the score forever.
    """
    n = len(field_tokens)
    average = float(avgdl) if avgdl else float(n or 1)
    if average <= 0:
        average = 1.0
    counts = Counter(field_tokens)
    length_penalty = 1 - b + b * (n / average)
    denominator_base = k1 * length_penalty
    total = 0.0
    maximum = 0.0
    for term in dict.fromkeys(query_tokens):
        term_idf = float(idf.get(term, 1.0)) if idf else 1.0
        maximum += term_idf
        tf = counts.get(term, 0)
        if tf:
            total += term_idf * (tf * (k1 + 1)) / (tf + denominator_base)
    coverage = total / maximum if maximum else 0.0
    return FieldScore(
        tokens=n,
        coverage=min(1.0, coverage),
        length_penalty=round(length_penalty, 4),
        bm25=round(total, 4),
    )


def has_exact_phrase(field_tokens: Sequence[str], query_tokens: Sequence[str]) -> bool:
    query = list(query_tokens)
    if not query or len(query) > len(field_tokens):
        return False
    width = len(query)
    first = query[0]
    for index, token in enumerate(field_tokens):
        if token == first and list(field_tokens[index : index + width]) == query:
            return True
    return False


def first_hit_index(field_tokens: Sequence[str], query_tokens: Sequence[str]) -> int:
    wanted = set(query_tokens)
    for index, token in enumerate(field_tokens):
        if token in wanted:
            return index
    return -1


def keyword_density(field_tokens: Sequence[str], query_tokens: Sequence[str]) -> float:
    if not field_tokens:
        return 0.0
    counts = Counter(field_tokens)
    hits = sum(counts.get(term, 0) for term in dict.fromkeys(query_tokens))
    return hits / len(field_tokens)


def idf_from_corpus(
    documents: Sequence[Sequence[str]], query_terms: Iterable[str]
) -> Dict[str, float]:
    total = len(documents) or 1
    idf: Dict[str, float] = {}
    for term in dict.fromkeys(query_terms):
        df = sum(1 for document in documents if term in document)
        idf[term] = round(math.log(1 + (total - df + 0.5) / (df + 0.5)), 6)
    return idf


def average_length(documents: Sequence[Sequence[str]]) -> Optional[float]:
    if not documents:
        return None
    return sum(len(document) for document in documents) / len(documents)


def slugify(keyword: str) -> str:
    normalized = normalize_text(keyword)
    parts = WORD_RE.findall(normalized)
    if parts:
        return "-".join(parts)
    compact = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return compact or "page"
