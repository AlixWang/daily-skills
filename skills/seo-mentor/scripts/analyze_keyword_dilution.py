#!/usr/bin/env python3
"""analyze_keyword_dilution.py - measure per-page keyword dilution.

Models the first two dilution layers from the SEO diagnosis playbook:

1. field-level BM25 length normalization on <title> and <h1> plus exact-phrase
   continuity (the "denominator inflation" and "phrase split" problem);
2. intent purity across several target keywords (a proxy for semantic centroid
   drift when one page chases three intents).

Output is stable JSON so the report template and the regression tests can both
consume it. The model is heuristic; see references/keyword_dilution_model.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.seo_text import (  # noqa: E402
    average_length,
    bm25_field,
    count_words,
    extract_page,
    first_hit_index,
    has_exact_phrase,
    idf_from_corpus,
    keyword_density,
    slugify,
    tokenize,
)

FIELD_WEIGHTS = {"title": 0.6, "h1": 0.3, "body": 0.1}
PURITY_WEIGHTS = {"title": 0.5, "h1": 0.3, "body": 0.2}
DILUTED_BELOW = 0.5
FOCUSED_AT = 0.75
TITLE_PENALTY_LIMIT = 1.3
BODY_DENSITY_FLOOR = 0.003
CONFLICT_GAP = 0.10
CONFLICT_FLOOR = 0.30


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def score_keyword(
    keyword: str,
    page_tokens: Dict[str, List[str]],
    params: Dict[str, object],
    idf: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    query = tokenize(keyword)
    k1 = float(params["k1"])
    b = float(params["b"])
    avgdl_title = float(params["avgdl_title"])
    avgdl_h1 = float(params["avgdl_h1"])
    avgdl_body = params.get("avgdl_body")

    title_tokens = page_tokens["title"]
    h1_tokens = page_tokens["h1"]
    body_tokens = page_tokens["body"]

    title_score = bm25_field(title_tokens, query, k1, b, avgdl_title, idf)
    h1_score = bm25_field(h1_tokens, query, k1, b, avgdl_h1, idf)
    body_avgdl = float(avgdl_body) if avgdl_body else float(len(body_tokens) or 1)
    body_score = bm25_field(body_tokens, query, k1, b, body_avgdl, idf)

    title_phrase = has_exact_phrase(title_tokens, query)
    h1_phrase = has_exact_phrase(h1_tokens, query)
    title_relevance = title_score.coverage * (1.0 if title_phrase else 0.5)
    h1_relevance = h1_score.coverage * (1.0 if h1_phrase else 0.5)
    body_relevance = body_score.coverage

    relevance = (
        FIELD_WEIGHTS["title"] * title_relevance
        + FIELD_WEIGHTS["h1"] * h1_relevance
        + FIELD_WEIGHTS["body"] * body_relevance
    )
    dilution = max(0.0, 1.0 - relevance)
    if relevance < DILUTED_BELOW:
        verdict = "DILUTED"
    elif relevance < FOCUSED_AT:
        verdict = "PARTIAL"
    else:
        verdict = "FOCUSED"

    purity_input = (
        PURITY_WEIGHTS["title"] * title_score.coverage
        + PURITY_WEIGHTS["h1"] * h1_score.coverage
        + PURITY_WEIGHTS["body"] * body_score.coverage
    )

    return {
        "keyword": keyword,
        "tokens": list(dict.fromkeys(query)),
        "fields": {
            "title": {
                "tokens": title_score.tokens,
                "length_penalty": title_score.length_penalty,
                "coverage": _round(title_score.coverage),
                "exact_phrase": title_phrase,
                "position": first_hit_index(title_tokens, query),
                "relevance": _round(title_relevance),
            },
            "h1": {
                "tokens": h1_score.tokens,
                "length_penalty": h1_score.length_penalty,
                "coverage": _round(h1_score.coverage),
                "exact_phrase": h1_phrase,
                "position": first_hit_index(h1_tokens, query),
                "relevance": _round(h1_relevance),
            },
            "body": {
                "tokens": body_score.tokens,
                "length_penalty": body_score.length_penalty,
                "coverage": _round(body_score.coverage),
                "exact_phrase": has_exact_phrase(body_tokens, query),
                "density": _round(keyword_density(body_tokens, query)),
                "relevance": _round(body_relevance),
            },
        },
        "relevance": _round(relevance),
        "dilution_index": _round(dilution),
        "verdict": verdict,
        "_purity_input": purity_input,
    }


def apply_intent_purity(keywords: List[Dict[str, object]]) -> List[Dict[str, object]]:
    total = sum(float(item["_purity_input"]) for item in keywords)
    for item in keywords:
        purity = float(item["_purity_input"]) / total if total else 0.0
        item["intent_purity"] = _round(purity)
        del item["_purity_input"]
    return keywords


def detect_conflicts(keywords: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    ranked = sorted(keywords, key=lambda item: item["intent_purity"], reverse=True)
    if len(ranked) < 2:
        return []
    gap = float(ranked[0]["intent_purity"]) - float(ranked[1]["intent_purity"])
    if gap < CONFLICT_GAP and float(ranked[1]["intent_purity"]) >= CONFLICT_FLOOR:
        return [
            {
                "type": "multi_intent",
                "keywords": [ranked[0]["keyword"], ranked[1]["keyword"]],
                "gap": _round(gap),
                "detail": "两个意图的覆盖度几乎持平，页面语义重心落在两者之间。",
            }
        ]
    return []


def build_findings(
    page, keywords: Sequence[Dict[str, object]], conflicts, title_penalty: float
) -> List[Dict[str, object]]:
    findings: List[Dict[str, object]] = []

    def add(check_id: str, severity: str, field: str, message: str) -> None:
        findings.append(
            {"id": check_id, "severity": severity, "field": field, "message": message}
        )

    if not page.title:
        add("KWD-00", "HIGH", "title", "页面缺少 <title>，无法参与任何标题相关性计算。")
    if not page.h1:
        add("KWD-00", "HIGH", "h1", "页面缺少 <h1>，主标题权重位空缺。")

    if title_penalty > TITLE_PENALTY_LIMIT:
        add(
            "KWD-03",
            "MEDIUM",
            "title",
            f"Title 长度惩罚系数 {title_penalty:.2f} > {TITLE_PENALTY_LIMIT}，"
            "字段分母膨胀，单词分摊权重被折算。",
        )

    for item in keywords:
        name = item["keyword"]
        fields = item["fields"]
        if page.title and not fields["title"]["exact_phrase"]:
            add(
                "KWD-01",
                "HIGH",
                "title",
                f"目标词 “{name}” 未在 Title 中连续出现，只能拿到零散单词分。",
            )
        if page.h1 and not fields["h1"]["exact_phrase"]:
            add(
                "KWD-02",
                "MEDIUM",
                "h1",
                f"目标词 “{name}” 未在 H1 中连续出现。",
            )
        if page.h1 and fields["h1"]["coverage"] < 1.0:
            add(
                "KWD-04",
                "MEDIUM",
                "h1",
                f"H1 未覆盖 “{name}” 的全部词项（覆盖率 {fields['h1']['coverage']:.2f}）。",
            )
        if page.body and fields["body"]["density"] < BODY_DENSITY_FLOOR:
            add(
                "KWD-05",
                "LOW",
                "body",
                f"正文关键词密度 {fields['body']['density'] * 100:.2f}% 低于 "
                f"{BODY_DENSITY_FLOOR * 100:.1f}%，语义支撑不足。",
            )

    if conflicts:
        names = " / ".join(conflicts[0]["keywords"])
        add(
            "KWD-06",
            "HIGH",
            "page",
            f"多意图冲突：{names} 的覆盖度差距仅 {conflicts[0]['gap']:.2f}，"
            "页面试图同时讨好多个意图。",
        )
    return findings


def build_recommendations(
    page,
    keywords: Sequence[Dict[str, object]],
    conflicts,
    primary: str,
    title_penalty: float,
) -> List[Dict[str, object]]:
    recommendations: List[Dict[str, object]] = []
    primary_item = next((item for item in keywords if item["keyword"] == primary), None)

    if primary_item and not primary_item["fields"]["title"]["exact_phrase"]:
        recommendations.append(
            {
                "action": "front_load_phrase",
                "keyword": primary,
                "detail": f"把 “{primary}” 原样连续放进 Title 前 3 个词，保留完整词序。",
            }
        )

    if title_penalty > TITLE_PENALTY_LIMIT:
        recommendations.append(
            {
                "action": "trim_title",
                "max_tokens": max(3, int(round(float(TITLE_PENALTY_LIMIT) * 6))),
                "detail": "把次要修饰词（如格式名、卖点）移出 Title，改由 H1 或副标题承载。",
            }
        )

    split_targets = [
        item
        for item in keywords
        if item["keyword"] != primary and float(item["intent_purity"]) < 0.15
    ]
    for item in split_targets:
        recommendations.append(
            {
                "action": "split_page",
                "keyword": item["keyword"],
                "suggested_path": "/" + slugify(str(item["keyword"])),
                "detail": "该意图在首页只分到极低权重，拆成独立工具落地页单独承接。",
            }
        )

    if conflicts and not split_targets:
        loser = min(keywords, key=lambda item: item["intent_purity"])
        recommendations.append(
            {
                "action": "split_page",
                "keyword": loser["keyword"],
                "suggested_path": "/" + slugify(str(loser["keyword"])),
                "detail": "把冲突意图中较弱的一个剥离到独立页面，首页只保留主词。",
            }
        )
    return recommendations


def analyze(
    html: str,
    keywords: Sequence[str],
    primary: Optional[str],
    params: Dict[str, object],
    source: str = "",
    corpus: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    page = extract_page(html)
    page_tokens = {
        "title": tokenize(page.title),
        "h1": tokenize(page.h1),
        "body": tokenize(page.body),
    }

    idf = None
    corpus_average = None
    if corpus:
        documents = [tokenize(line) for line in corpus if line.strip()]
        query_terms: List[str] = []
        for keyword in keywords:
            query_terms.extend(tokenize(keyword))
        idf = idf_from_corpus(documents, query_terms)
        corpus_average = average_length(documents)

    if not params.get("avgdl_title"):
        params["avgdl_title"] = round(corpus_average, 2) if corpus_average else 6.0
    if not params.get("avgdl_h1"):
        params["avgdl_h1"] = 5.0

    scored = [score_keyword(keyword, page_tokens, params, idf) for keyword in keywords]
    scored = apply_intent_purity(scored)
    conflicts = detect_conflicts(scored)

    primary_name = primary or (keywords[0] if keywords else "")
    title_penalty = max(
        (float(item["fields"]["title"]["length_penalty"]) for item in scored), default=0.0
    )

    report = {
        "version": 1,
        "page": {
            "file": source,
            "title": page.title,
            "h1": page.h1,
            "meta_description": page.meta_description,
            "title_tokens": len(page_tokens["title"]),
            "h1_tokens": len(page_tokens["h1"]),
            "word_count": page.word_count or count_words(page.body),
            "first_paragraph": page.first_paragraph,
        },
        "params": {
            "k1": float(params["k1"]),
            "b": float(params["b"]),
            "avgdl_title": float(params["avgdl_title"]),
            "avgdl_h1": float(params["avgdl_h1"]),
            "avgdl_body": params.get("avgdl_body"),
            "idf_mode": "corpus" if idf else "uniform",
        },
        "primary": primary_name,
        "keywords": scored,
        "conflicts": conflicts,
        "findings": build_findings(page, scored, conflicts, title_penalty),
        "recommendations": build_recommendations(
            page, scored, conflicts, primary_name, title_penalty
        ),
    }
    return report


def _print_human(report: Dict[str, object]) -> None:
    page = report["page"]
    print("=" * 78)
    print(f"  Keyword dilution report: {page['title'] or '(no title)'}")
    print(f"  H1: {page['h1'] or '(no h1)'}  |  words: {page['word_count']}")
    print("=" * 78)
    header = f"{'keyword':<28}{'relevance':>10}{'dilution':>10}{'purity':>8}  verdict"
    print(header)
    for item in report["keywords"]:
        print(
            f"{str(item['keyword'])[:27]:<28}{item['relevance']:>10.3f}"
            f"{item['dilution_index']:>10.3f}{item['intent_purity']:>8.2f}  {item['verdict']}"
        )
    findings = report["findings"]
    if findings:
        print(f"\nFindings ({len(findings)}):")
        for finding in findings:
            print(f"  [{finding['severity']:<6}] {finding['id']} {finding['message']}")
    recommendations = report["recommendations"]
    if recommendations:
        print("\nRecommendations:")
        for item in recommendations:
            target = item.get("keyword") or item.get("action")
            print(f"  - {item['action']}: {target} -> {item.get('detail', '')}")
    print()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure per-page keyword dilution (BM25 field penalty + phrase continuity + intent purity)."
    )
    parser.add_argument("-f", "--file", required=True, help="Path to the HTML file to analyze.")
    parser.add_argument(
        "-k",
        "--keyword",
        action="append",
        required=True,
        help="Target keyword. Repeat the flag or pass a comma separated list.",
    )
    parser.add_argument("--primary", help="Primary keyword. Defaults to the first -k value.")
    parser.add_argument("--k1", type=float, default=1.2)
    parser.add_argument("--b", type=float, default=0.75)
    parser.add_argument("--avgdl-title", type=float, default=None)
    parser.add_argument("--avgdl-h1", type=float, default=None)
    parser.add_argument("--avgdl-body", type=float, default=None)
    parser.add_argument(
        "--corpus",
        help="Optional text file with one competing title per line, used for IDF and avgdl.",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=None,
        help="Exit with status 1 when the primary keyword relevance is below this value.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine readable JSON.")
    args = parser.parse_args(argv)

    keywords: List[str] = []
    for raw in args.keyword:
        for part in str(raw).split(","):
            cleaned = part.strip()
            if cleaned and cleaned not in keywords:
                keywords.append(cleaned)
    if not keywords:
        print("Error: at least one non-empty keyword is required.", file=sys.stderr)
        return 2

    path = Path(args.file)
    if not path.is_file():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2
    html = path.read_text(encoding="utf-8", errors="replace")

    corpus = None
    if args.corpus:
        corpus_path = Path(args.corpus)
        if not corpus_path.is_file():
            print(f"Error: corpus not found: {args.corpus}", file=sys.stderr)
            return 2
        corpus = corpus_path.read_text(encoding="utf-8", errors="replace").splitlines()

    params: Dict[str, object] = {
        "k1": args.k1,
        "b": args.b,
        "avgdl_title": args.avgdl_title,
        "avgdl_h1": args.avgdl_h1,
        "avgdl_body": args.avgdl_body,
    }

    report = analyze(html, keywords, args.primary, params, source=str(path), corpus=corpus)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _print_human(report)

    if args.fail_under is not None:
        primary = report["primary"]
        item = next(
            (entry for entry in report["keywords"] if entry["keyword"] == primary), None
        )
        if item and float(item["relevance"]) < args.fail_under:
            print(
                f"FAIL: primary keyword “{primary}” relevance {item['relevance']} "
                f"< --fail-under {args.fail_under}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
