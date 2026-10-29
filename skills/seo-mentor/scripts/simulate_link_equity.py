#!/usr/bin/env python3
"""simulate_link_equity.py - quantify internal link equity dilution.

Models the third dilution layer: one pool of external authority spread across
many URLs. Given a site topology, the script runs a damped PageRank iteration
over the internal link graph and reports the share each page receives, plus a
before/after comparison against a focused subset (usually the English core).

The numbers are a topology simulation, not a crawl of Google's index. See
references/keyword_dilution_model.md for the assumptions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

DEFAULT_DAMPING = 0.85
DEFAULT_EXTERNAL_WEIGHT = 1.0
DEFAULT_INDEX_QUOTA = 200
DEFAULT_MAX_PAGES = 20000


def _pct(value: float) -> float:
    return round(value * 100, 4)


def pagerank(
    urls: Sequence[str],
    edges: Dict[str, Sequence[str]],
    damping: float = DEFAULT_DAMPING,
    external_weight: float = DEFAULT_EXTERNAL_WEIGHT,
    home: Optional[str] = None,
    tolerance: float = 1e-9,
    max_iterations: int = 200,
) -> Tuple[Dict[str, float], int]:
    """Damped PageRank with dangling-node redistribution and normalized shares."""
    count = len(urls)
    if count == 0:
        return {}, 0
    index = {url: position for position, url in enumerate(urls)}
    out: List[List[int]] = []
    for url in urls:
        out.append([index[target] for target in edges.get(url, ()) if target in index])

    ranks = [1.0 / count] * count
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        updated = [(1 - damping) / count] * count
        dangling = sum(ranks[i] for i in range(count) if not out[i])
        for i, targets in enumerate(out):
            if not targets:
                continue
            share = damping * ranks[i] / len(targets)
            for target in targets:
                updated[target] += share
        if dangling:
            spread = damping * dangling / count
            for i in range(count):
                updated[i] += spread
        if home is not None and home in index:
            updated[index[home]] += (1 - damping) * external_weight
        delta = sum(abs(a - b) for a, b in zip(updated, ranks))
        ranks = updated
        if delta < tolerance:
            break

    total = sum(ranks) or 1.0
    return {url: ranks[i] / total for i, url in enumerate(urls)}, iterations


def _normalize_pages(raw: Dict[str, object]) -> Tuple[List[Dict[str, object]], List[str]]:
    warnings: List[str] = []
    pages_raw = raw.get("pages")
    if not isinstance(pages_raw, list) or not pages_raw:
        raise ValueError("site JSON must contain a non-empty 'pages' array")

    pages: List[Dict[str, object]] = []
    seen = set()
    for entry in pages_raw:
        if not isinstance(entry, dict) or not entry.get("url"):
            raise ValueError("every page needs a 'url' field")
        url = str(entry["url"]).strip()
        if url in seen:
            raise ValueError(f"duplicate url in site JSON: {url}")
        seen.add(url)
        links = entry.get("links_to")
        if links is not None and not isinstance(links, list):
            raise ValueError(f"'links_to' must be a list for {url}")
        pages.append(
            {
                "url": url,
                "group": str(entry.get("group") or "default"),
                "links_to": [str(link) for link in links] if links is not None else None,
            }
        )

    urls = [page["url"] for page in pages]
    home = "/" if "/" in urls else urls[0]
    implicit = 0
    for page in pages:
        if page["links_to"] is None:
            implicit += 1
            if page["url"] == home:
                page["links_to"] = [url for url in urls if url != home]
            else:
                page["links_to"] = [home]
    if implicit:
        warnings.append(
            f"{implicit} page(s) had no explicit 'links_to'; a star topology "
            "(home <-> every page) was assumed."
        )
    return pages, warnings


def _edges_for(
    pages: Sequence[Dict[str, object]], allowed: Optional[Iterable[str]] = None
) -> Dict[str, List[str]]:
    allowed_set = set(allowed) if allowed is not None else None
    edges: Dict[str, List[str]] = {}
    for page in pages:
        targets = []
        for target in page["links_to"] or []:
            if allowed_set is not None and target not in allowed_set:
                continue
            targets.append(target)
        edges[str(page["url"])] = targets
    return edges


def _average_share(
    shares: Dict[str, float], urls: Sequence[str], home: Optional[str]
) -> Optional[float]:
    values = [shares[url] for url in urls if url in shares and url != home]
    if not values:
        values = [shares[url] for url in urls if url in shares]
    if not values:
        return None
    return sum(values) / len(values)


def analyze_site(
    raw: Dict[str, object],
    damping: float = DEFAULT_DAMPING,
    external_weight: float = DEFAULT_EXTERNAL_WEIGHT,
    index_quota: int = DEFAULT_INDEX_QUOTA,
    compare_group: Optional[str] = None,
    core_group: str = "en-core",
    include_groups: Optional[Sequence[str]] = None,
    exclude_groups: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    pages, warnings = _normalize_pages(raw)

    if include_groups:
        pages = [page for page in pages if page["group"] in include_groups]
        if not pages:
            raise ValueError("--include-group filtered out every page")
    if exclude_groups:
        pages = [page for page in pages if page["group"] not in exclude_groups]
        if not pages:
            raise ValueError("--exclude-group filtered out every page")

    urls = [str(page["url"]) for page in pages]
    home = "/" if "/" in urls else urls[0]
    edges = _edges_for(pages, urls)

    unknown = sorted(
        {target for targets in edges.values() for target in targets if target not in set(urls)}
    )
    if unknown:
        warnings.append(f"{len(unknown)} link target(s) not present in the page set were dropped.")

    shares, iterations = pagerank(
        urls, edges, damping=damping, external_weight=external_weight, home=home
    )

    inlinks: Dict[str, int] = {url: 0 for url in urls}
    for targets in edges.values():
        for target in targets:
            if target in inlinks:
                inlinks[target] += 1

    group_stats: Dict[str, Dict[str, object]] = {}
    for page in pages:
        url = str(page["url"])
        group = str(page["group"])
        bucket = group_stats.setdefault(
            group, {"group": group, "pages": 0, "share_pct": 0.0, "urls": []}
        )
        bucket["pages"] = int(bucket["pages"]) + 1
        bucket["share_pct"] = float(bucket["share_pct"]) + _pct(shares.get(url, 0.0))
        bucket["urls"].append(url)

    groups = []
    for bucket in group_stats.values():
        page_count = int(bucket["pages"])
        groups.append(
            {
                "group": bucket["group"],
                "pages": page_count,
                "share_pct": round(float(bucket["share_pct"]), 4),
                "avg_share_pct": round(float(bucket["share_pct"]) / page_count, 4)
                if page_count
                else 0.0,
            }
        )
    groups.sort(key=lambda item: item["share_pct"], reverse=True)

    page_rows = [
        {
            "url": url,
            "group": next(page["group"] for page in pages if page["url"] == url),
            "share_pct": _pct(shares.get(url, 0.0)),
            "inlinks": inlinks.get(url, 0),
            "outlinks": len(edges.get(url, ())),
        }
        for url in urls
    ]
    page_rows.sort(key=lambda item: item["share_pct"], reverse=True)

    total_pages = len(urls)
    quota_pressure = round(total_pages / index_quota, 3) if index_quota else 0.0
    totals = {
        "pages": total_pages,
        "groups": len(groups),
        "index_quota": index_quota,
        "quota_pressure": quota_pressure,
        "oversubscribed": total_pages > index_quota if index_quota else False,
        "prune_count": max(0, total_pages - index_quota) if index_quota else 0,
        "iterations": iterations,
    }

    comparison = None
    if compare_group:
        kept = [str(page["url"]) for page in pages if page["group"] == compare_group]
        if not kept:
            raise ValueError(f"--compare-group '{compare_group}' matched no pages")
        subset_pages = [page for page in pages if page["group"] == compare_group]
        subset_edges = _edges_for(subset_pages, kept)
        subset_shares, _ = pagerank(
            kept,
            subset_edges,
            damping=damping,
            external_weight=external_weight,
            home=home if home in kept else kept[0],
        )
        before = _average_share(shares, kept, home if home in kept else None)
        after = _average_share(subset_shares, kept, home if home in kept else None)
        gain = round(after / before, 2) if before and after else None
        comparison = {
            "include_group": compare_group,
            "pages_before": total_pages,
            "pages_after": len(kept),
            "avg_share_before_pct": _pct(before) if before is not None else None,
            "avg_share_after_pct": _pct(after) if after is not None else None,
            "focus_gain": gain,
            "excludes_home": home in kept,
        }

    recommendations = []
    if totals["oversubscribed"]:
        recommendations.append(
            {
                "action": "prune_or_noindex",
                "detail": f"当前 {total_pages} 页超出新站索引配额 {index_quota}，"
                f"需裁剪或 noindex {totals['prune_count']} 页后再放量。",
            }
        )
    non_core = [
        group
        for group in groups
        if group["group"] not in (core_group, "default")
    ]
    non_core_pages = sum(int(group["pages"]) for group in non_core)
    if total_pages and non_core_pages > total_pages * 0.5:
        smallest_share = min(group["avg_share_pct"] for group in non_core)
        share_ratio = round(non_core_pages / total_pages * 100, 1)
        recommendations.append(
            {
                "action": "noindex_group",
                "group": "non-core",
                "detail": f"非核心页共 {non_core_pages} 页，占全站 {share_ratio}%，"
                f"单页仅分到 {smallest_share}% 权重，建议先 noindex 或下线。",
            }
        )
    if comparison and comparison["focus_gain"] and comparison["focus_gain"] >= 10:
        recommendations.append(
            {
                "action": "consolidate",
                "detail": f"聚焦到 {comparison['include_group']} 后单页权重提升 "
                f"{comparison['focus_gain']} 倍，优先保核心页收录。",
            }
        )

    return {
        "version": 1,
        "site": raw.get("site") or "",
        "params": {
            "damping": damping,
            "external_weight": external_weight,
            "index_quota": index_quota,
            "core_group": core_group,
            "home": home,
        },
        "totals": totals,
        "groups": groups,
        "pages": page_rows,
        "comparison": comparison,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def _print_human(report: Dict[str, object]) -> None:
    totals = report["totals"]
    print("=" * 78)
    print(f"  Link equity simulation: {report['site'] or '(no site)'}")
    print(
        f"  pages: {totals['pages']}  |  groups: {totals['groups']}  |  "
        f"index quota: {totals['index_quota']}  |  pressure: {totals['quota_pressure']}x"
    )
    print("=" * 78)
    print(f"{'group':<24}{'pages':>8}{'share %':>12}{'avg/page %':>14}")
    for group in report["groups"]:
        print(
            f"{str(group['group'])[:23]:<24}{group['pages']:>8}"
            f"{group['share_pct']:>12.3f}{group['avg_share_pct']:>14.4f}"
        )
    print("\nTop pages by share:")
    for row in report["pages"][:10]:
        print(
            f"  {row['share_pct']:>8.4f}%  {row['url']:<40} in:{row['inlinks']:<5} "
            f"out:{row['outlinks']}"
        )
    comparison = report.get("comparison")
    if comparison:
        print("\nFocus comparison:")
        print(
            f"  group {comparison['include_group']}: "
            f"{comparison['pages_before']} -> {comparison['pages_after']} pages, "
            f"avg share {comparison['avg_share_before_pct']}% -> "
            f"{comparison['avg_share_after_pct']}% "
            f"(x{comparison['focus_gain']})"
        )
    for warning in report["warnings"]:
        print(f"\nWARN: {warning}")
    for item in report["recommendations"]:
        print(f"  - {item['action']}: {item['detail']}")
    print()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Simulate internal PageRank distribution and quantify page-count dilution."
    )
    parser.add_argument("-s", "--site", required=True, help="Path to the site topology JSON.")
    parser.add_argument(
        "--core-group",
        default="en-core",
        help="Group treated as the site core when flagging non-core dilution. Default en-core.",
    )
    parser.add_argument(
        "--compare-group",
        help="Group to re-simulate in isolation. Defaults to --core-group.",
    )
    parser.add_argument(
        "--include-group", action="append", default=[], help="Keep only this group. Repeatable."
    )
    parser.add_argument(
        "--exclude-group", action="append", default=[], help="Drop this group. Repeatable."
    )
    parser.add_argument("--damping", type=float, default=DEFAULT_DAMPING)
    parser.add_argument("--external-weight", type=float, default=DEFAULT_EXTERNAL_WEIGHT)
    parser.add_argument("--index-quota", type=int, default=DEFAULT_INDEX_QUOTA)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.site)
    if not path.is_file():
        print(f"Error: site JSON not found: {args.site}", file=sys.stderr)
        return 2
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as error:
        print(f"Error: invalid JSON in {args.site}: {error}", file=sys.stderr)
        return 2
    if not isinstance(raw, dict):
        print("Error: site JSON must be an object with a 'pages' array.", file=sys.stderr)
        return 2
    page_count = len(raw.get("pages") or [])
    if page_count > args.max_pages:
        print(
            f"Error: {page_count} pages exceeds --max-pages {args.max_pages}.",
            file=sys.stderr,
        )
        return 2

    try:
        report = analyze_site(
            raw,
            damping=args.damping,
            external_weight=args.external_weight,
            index_quota=args.index_quota,
            compare_group=args.compare_group or args.core_group,
            core_group=args.core_group,
            include_groups=args.include_group or None,
            exclude_groups=args.exclude_group or None,
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
