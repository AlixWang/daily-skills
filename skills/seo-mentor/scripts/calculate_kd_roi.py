#!/usr/bin/env python3
"""calculate_kd_roi.py - keyword investment/return scoring with a feasibility gate.

The raw score is unchanged from the original skill version:

    score = volume * cpc * intent_weight / (KD * dev_days)

On top of it, this version adds the authority gate the original script was
missing. A DR 1.4 new site cannot rank for a KD 78 head term no matter how large
the volume is, so such a keyword is reported as NO_GO / OFF_TARGET instead of
GOLD. The gate is a documented heuristic, not a Google metric.
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, Optional

INTENT_WEIGHTS = {
    "transactional": 1.5,
    "commercial": 1.2,
    "informational": 0.8,
    "navigational": 0.4,
}

# (KD ceiling, DR required to compete). New-site heuristics.
AUTHORITY_TIERS = (
    (20.0, 0.0),
    (30.0, 5.0),
    (45.0, 20.0),
    (60.0, 35.0),
    (float("inf"), 50.0),
)

DEFAULT_MAX_KD = 30.0


def required_dr(kd: float) -> float:
    for ceiling, dr in AUTHORITY_TIERS:
        if kd <= ceiling:
            return dr
    return AUTHORITY_TIERS[-1][1]


def _base_tag(score: float) -> tuple:
    if score >= 500:
        return "GOLD", "极高优先级（黄金小词/新词，立即开干）"
    if score >= 150:
        return "RECOMMENDED", "高性价比（推荐作为 MVP 第一梯队落地页）"
    if score >= 50:
        return "SECONDARY", "中等性价比（适合程序化 SEO 批量矩阵补充）"
    return "SKIP", "性价比低（竞争过大或搜索价值低，暂缓）"


def calculate_kd_roi(
    keyword: str,
    volume: float,
    kd: float,
    cpc: float = 1.0,
    intent: str = "transactional",
    dev_days: float = 1.0,
    dr: Optional[float] = None,
    relevance: Optional[float] = None,
    max_kd: float = DEFAULT_MAX_KD,
) -> Dict[str, object]:
    """Score a keyword and decide whether the site can realistically compete.

    ``dr`` is optional to keep the legacy call signature working. Without it the
    authority gate is reported as UNRATED, but the KD ceiling still applies.
    """
    intent_mult = INTENT_WEIGHTS.get(str(intent).lower(), 1.0)
    effective_kd = max(1.0, float(kd))
    effective_days = max(0.5, float(dev_days))
    score = (float(volume) * float(cpc) * intent_mult) / (effective_kd * effective_days)

    need = required_dr(effective_kd)
    reasons = []
    if effective_kd > float(max_kd):
        reasons.append("kd_ceiling")

    authority_gate = "UNRATED"
    authority_gap: Optional[float] = None
    authority_factor: Optional[float] = None
    if dr is not None:
        authority_gap = round(need - float(dr), 2)
        authority_gate = "PASS" if float(dr) >= need else "FAIL"
        authority_factor = round(min(1.0, (float(dr) + 1) / 20), 4)
        if authority_gate == "FAIL":
            reasons.append("authority_gap")

    verdict = "NO_GO" if reasons else "GO"
    tag, recommendation = _base_tag(score)
    if verdict == "NO_GO":
        tag = "OFF_TARGET"
        if "kd_ceiling" in reasons and "authority_gap" in reasons:
            recommendation = (
                f"KD {effective_kd:g} 超过新站上限 {float(max_kd):g}，且当前 DR {float(dr):g} "
                f"低于所需 {need:g}；先做 KD≤{float(max_kd):g} 的长尾词并补外链。"
            )
        elif "kd_ceiling" in reasons:
            recommendation = (
                f"KD {effective_kd:g} 超过新站上限 {float(max_kd):g}，"
                f"先做 KD≤{float(max_kd):g} 的长尾词，或显式放宽 --max-kd。"
            )
        else:
            recommendation = (
                f"当前 DR {float(dr):g} 低于该词所需 DR {need:g}，"
                "先补外链或换更低的 KD 词。"
            )

    projected = score
    if relevance is not None:
        projected *= float(relevance)
    if authority_factor is not None:
        projected *= authority_factor

    return {
        "keyword": keyword,
        "volume": volume,
        "kd": kd,
        "cpc": cpc,
        "intent": intent,
        "dev_days": dev_days,
        "dr": dr,
        "score": round(score, 2),
        "tag": tag,
        "verdict": verdict,
        "reason": "+".join(reasons) if reasons else "ok",
        "required_dr": need,
        "authority_gate": authority_gate,
        "authority_gap": authority_gap,
        "authority_factor": authority_factor,
        "relevance": relevance,
        "projected_score": round(projected, 2),
        "recommendation": recommendation,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Keyword ROI scoring with a KD ceiling and DR feasibility gate."
    )
    parser.add_argument("-k", "--keyword", required=True)
    parser.add_argument("-v", "--volume", type=float, required=True)
    parser.add_argument("-d", "--kd", type=float, required=True)
    parser.add_argument("-c", "--cpc", type=float, default=1.0)
    parser.add_argument("-i", "--intent", default="transactional")
    parser.add_argument("-t", "--dev-days", type=float, default=1.0)
    parser.add_argument(
        "-a", "--dr", type=float, default=None, help="Domain Rating of the target site."
    )
    parser.add_argument(
        "--relevance",
        type=float,
        default=None,
        help="Optional relevance from analyze_keyword_dilution.py (0..1).",
    )
    parser.add_argument(
        "--max-kd",
        type=float,
        default=DEFAULT_MAX_KD,
        help="Hard KD ceiling for a new site. Default 30.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = calculate_kd_roi(
        args.keyword,
        args.volume,
        args.kd,
        args.cpc,
        args.intent,
        args.dev_days,
        dr=args.dr,
        relevance=args.relevance,
        max_kd=args.max_kd,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
