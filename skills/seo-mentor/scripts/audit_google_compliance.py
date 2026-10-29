#!/usr/bin/env python3
"""
audit_google_compliance.py - Google Search Central & GEO (Generative Engine Optimization) Audit Tool.
Automated compliance checker for traditional Google SEO, Core Web Vitals risks, and AI Search / LLM citability.
"""

import sys
import re
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.seo_text import (  # noqa: E402
    extract_page,
    has_exact_phrase,
    keyword_density,
    tokenize,
)

SCRIPTS_DIR = Path(__file__).resolve().parent
TITLE_AVGDL = 6.0


def _require_bs4():
    try:
        from bs4 import BeautifulSoup  # noqa: WPS433
    except ImportError:
        print(
            "Error: beautifulsoup4 is required for the full HTML audit.\n"
            f"  python3 -m pip install -r {SCRIPTS_DIR / 'requirements.txt'}\n"
            "  (--keyword-only does not need it)",
            file=sys.stderr,
        )
        raise SystemExit(3)
    return BeautifulSoup


def audit_keyword_targeting(html_content, target_keyword, avgdl_title=TITLE_AVGDL):
    """Keyword-level checks that the original -k flag never actually performed."""
    results = []
    if not target_keyword:
        return results

    page = extract_page(html_content)
    query = tokenize(target_keyword)
    if not query:
        return results
    unique = list(dict.fromkeys(query))
    title_tokens = tokenize(page.title)
    h1_tokens = tokenize(page.h1)
    body_tokens = tokenize(page.body)

    def add(check_id, name, status, impact, message, evidence=None):
        results.append(
            {
                "category": "Keyword Targeting",
                "id": check_id,
                "name": name,
                "status": status,
                "score_impact": impact,
                "message": message,
                "evidence": evidence,
            }
        )

    missing = [term for term in unique if term not in set(title_tokens)]
    if not page.title:
        add("KWD-01", "Keyword in Title", "FAIL", -10, "Missing <title>; keyword cannot be matched.")
    elif missing:
        add(
            "KWD-01",
            "Keyword in Title",
            "FAIL",
            -8,
            f"Title misses {missing} from “{target_keyword}”.",
            page.title,
        )
    else:
        add(
            "KWD-01",
            "Keyword in Title",
            "PASS",
            0,
            f"Title covers all {len(unique)} query term(s).",
            page.title,
        )

    if page.title:
        if has_exact_phrase(title_tokens, query):
            add("KWD-02", "Exact Phrase in Title", "PASS", 0, f"“{target_keyword}” appears contiguously.")
        else:
            add(
                "KWD-02",
                "Exact Phrase in Title",
                "WARN",
                -4,
                f"“{target_keyword}” never appears contiguously in the title.",
            )

    if not page.h1:
        add("KWD-03", "Keyword in H1", "FAIL", -6, "Missing <h1>; primary heading slot is empty.")
    elif [term for term in unique if term not in set(h1_tokens)]:
        add(
            "KWD-03",
            "Keyword in H1",
            "WARN",
            -5,
            f"H1 does not cover “{target_keyword}”.",
            page.h1,
        )
    else:
        add("KWD-03", "Keyword in H1", "PASS", 0, "H1 covers the full query.", page.h1)

    head_tokens = body_tokens[:100]
    if has_exact_phrase(head_tokens, query):
        add("KWD-04", "Keyword in First 100 Words", "PASS", 0, "Exact phrase found in the opening 100 words.")
    else:
        add(
            "KWD-04",
            "Keyword in First 100 Words",
            "WARN",
            -3,
            "Exact phrase not found in the opening 100 words.",
        )

    title_penalty = 1 - 0.75 + 0.75 * (len(title_tokens) / avgdl_title if avgdl_title else 1)
    if len(title_tokens) > avgdl_title * 1.3:
        add(
            "KWD-05",
            "Title Field Budget",
            "WARN",
            -3,
            f"Title has {len(title_tokens)} tokens (budget {avgdl_title * 1.3:.1f}, "
            f"length penalty {title_penalty:.2f}).",
        )
    else:
        add(
            "KWD-05",
            "Title Field Budget",
            "PASS",
            0,
            f"Title length is within budget ({len(title_tokens)} tokens).",
        )

    density = keyword_density(body_tokens, query)
    if 0.005 <= density <= 0.03:
        add("KWD-06", "Body Keyword Density", "PASS", 0, f"Density {density * 100:.2f}% is in the 0.5%-3% band.")
    else:
        add(
            "KWD-06",
            "Body Keyword Density",
            "WARN",
            -3,
            f"Density {density * 100:.2f}% is outside the 0.5%-3% band.",
        )

    return results


def audit_html(html_content, target_keyword=None, check_geo=True):
    BeautifulSoup = _require_bs4()
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    results.extend(audit_keyword_targeting(html_content, target_keyword))

    def add_res(category, check_id, name, status, score_impact, message, evidence=None):
        results.append({
            "category": category,
            "id": check_id,
            "name": name,
            "status": status, # PASS, WARN, FAIL
            "score_impact": score_impact,
            "message": message,
            "evidence": evidence
        })

    # --- 1. Traditional Google SEO & Technical Head Checks ---
    # Title
    titles = soup.find_all('title')
    if not titles:
        add_res("Technical SEO", "CORE-01", "Page Title", "FAIL", -10, "Missing <title> tag in <head>.")
    elif len(titles) > 1:
        add_res("Technical SEO", "CORE-01", "Page Title", "FAIL", -5, f"Multiple <title> tags found ({len(titles)}).")
    else:
        title_text = titles[0].get_text(strip=True)
        length = len(title_text)
        if 30 <= length <= 65:
            add_res("Technical SEO", "CORE-02", "Title Length", "PASS", 0, f"Title length optimal ({length} chars).", title_text)
        elif length < 30:
            add_res("Technical SEO", "CORE-02", "Title Length", "WARN", -2, f"Title too short ({length} chars, recommended 30-65).", title_text)
        else:
            add_res("Technical SEO", "CORE-02", "Title Length", "WARN", -2, f"Title may be truncated ({length} chars > 65).", title_text)

    # Meta Description
    meta_desc = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
    if not meta_desc or not meta_desc.get('content'):
        add_res("Technical SEO", "CORE-03", "Meta Description", "FAIL", -8, "Missing meta description tag.")
    else:
        desc_text = meta_desc['content'].strip()
        length = len(desc_text)
        if 110 <= length <= 165:
            add_res("Technical SEO", "CORE-04", "Meta Description Length", "PASS", 0, f"Description length optimal ({length} chars).", desc_text)
        elif length < 110:
            add_res("Technical SEO", "CORE-04", "Meta Description Length", "WARN", -2, f"Description short ({length} chars, recommended 120-160).", desc_text)
        else:
            add_res("Technical SEO", "CORE-04", "Meta Description Length", "WARN", -2, f"Description long ({length} chars > 165, risk of truncation).", desc_text)

    # Canonical
    canonical = soup.find('link', rel=lambda x: x and 'canonical' in x.lower())
    if not canonical or not canonical.get('href'):
        add_res("Technical SEO", "CORE-05", "Canonical Link", "FAIL", -5, "Missing rel=canonical link.")
    else:
        href = canonical['href'].strip()
        if href.startswith('http://') or href.startswith('https://'):
            add_res("Technical SEO", "CORE-06", "Canonical Target", "PASS", 0, "Canonical is a full absolute URL.", href)
        else:
            add_res("Technical SEO", "CORE-06", "Canonical Target", "FAIL", -5, "Canonical is relative, must be an absolute URL.", href)

    # Viewport
    viewport = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'viewport'})
    if viewport and 'width=device-width' in viewport.get('content', ''):
        add_res("Technical SEO", "CORE-10", "Mobile Viewport", "PASS", 0, "Mobile-friendly viewport declared.")
    else:
        add_res("Technical SEO", "CORE-10", "Mobile Viewport", "FAIL", -10, "Missing or invalid mobile viewport declaration.")

    # H1 Heading
    h1s = soup.find_all('h1')
    if not h1s:
        add_res("Technical SEO", "CORE-12", "H1 Heading", "FAIL", -10, "Page has no <h1> heading.")
    elif len(h1s) > 1:
        add_res("Technical SEO", "CORE-13", "Single H1", "WARN", -3, f"Multiple <h1> headings found ({len(h1s)}). Exactly one recommended.")
    else:
        add_res("Technical SEO", "CORE-12", "H1 Heading", "PASS", 0, "Single H1 present.", h1s[0].get_text(strip=True))

    # --- 2. Performance & Frontend Quality ---
    # Inline JS weight
    inline_scripts = soup.find_all('script', src=False)
    inline_js_size = sum(len(s.string or '') for s in inline_scripts)
    inline_js_kb = round(inline_js_size / 1024, 1)
    if inline_js_kb <= 20:
        add_res("Performance", "PERF-14", "Inline JavaScript Size", "PASS", 0, f"Inline JS payload light ({inline_js_kb} KiB <= 20 KiB).")
    elif inline_js_kb <= 50:
        add_res("Performance", "PERF-14", "Inline JavaScript Size", "WARN", -3, f"Inline JS moderate ({inline_js_kb} KiB). Consider external caching.")
    else:
        add_res("Performance", "PERF-14", "Inline JavaScript Size", "FAIL", -6, f"Heavy inline JS ({inline_js_kb} KiB > 50 KiB). Extracts to external cached bundle recommended.")

    # Accessibility Skip Link
    first_few_links = soup.find_all('a', limit=4)
    has_skip = any('skip' in (a.get_text(strip=True).lower() + (a.get('href') or '').lower()) for a in first_few_links)
    if has_skip:
        add_res("Accessibility", "A11Y-05", "Skip to Content Link", "PASS", 0, "Skip to content link found among first elements.")
    else:
        add_res("Accessibility", "A11Y-05", "Skip to Content Link", "WARN", -1, "No 'Skip to content' anchor found among initial links.")

    # --- 3. GEO & AI Citability Checks (geo.new alignment) ---
    if check_geo:
        # A. Images & LCP Lazy-loading check (IMG-05 / LAB-05)
        images = soup.find_all('img')
        if images:
            first_three = images[:3]
            lazy_in_first = [img for img in first_three if img.get('loading') == 'lazy']
            if lazy_in_first:
                add_res("AI Access & Perf", "IMG-05", "LCP Lazy Loading Placement", "FAIL", -8,
                        f"{len(lazy_in_first)} of first 3 images are lazy-loaded. Above-the-fold images MUST be eager loaded to avoid LCP delay.")
            else:
                add_res("AI Access & Perf", "IMG-05", "LCP Lazy Loading Placement", "PASS", 0, "Initial visible images load eagerly.")

            # Modern image format ratio (IMG-06)
            modern_exts = ('.webp', '.avif', '.svg')
            legacy_count = 0
            modern_count = 0
            for img in images:
                src = (img.get('src') or '').lower()
                if any(src.endswith(ext) or ext in src for ext in modern_exts):
                    modern_count += 1
                elif any(src.endswith(ext) for ext in ('.png', '.jpg', '.jpeg')):
                    legacy_count += 1
            total_checked = modern_count + legacy_count
            if total_checked > 0:
                modern_ratio = round((modern_count / total_checked) * 100)
                if modern_ratio >= 75:
                    add_res("AI Access & Perf", "IMG-06", "Modern Image Formats", "PASS", 0, f"{modern_ratio}% images use WebP/AVIF/SVG ({modern_count}/{total_checked}).")
                else:
                    add_res("AI Access & Perf", "IMG-06", "Modern Image Formats", "WARN", -4, f"Only {modern_ratio}% modern formats ({modern_count}/{total_checked}). Convert PNG/JPG to WebP/AVIF.")

        # B. Content Depth (EAT-05)
        # Extract main text
        main_tag = soup.find('main') or soup.find('article') or soup.body
        body_text = main_tag.get_text(separator=' ', strip=True) if main_tag else ""
        words = re.findall(r'\b[a-zA-Z0-9_\-\'\.]+\b', body_text)
        word_count = len(words)
        if word_count >= 300:
            add_res("Content & E-E-A-T", "EAT-05", "Content Depth (Word Count)", "PASS", 0, f"Adequate content depth ({word_count} words >= 300).")
        elif word_count >= 100:
            add_res("Content & E-E-A-T", "EAT-05", "Content Depth (Word Count)", "WARN", -5, f"Content is thin ({word_count} words < 300). Expand functional descriptions.")
        else:
            add_res("Content & E-E-A-T", "EAT-05", "Content Depth (Word Count)", "FAIL", -12, f"Critical thin content ({word_count} words < 100). High risk of unindexable rating.")

        # C. Link Density in Main Content (CONT-08)
        if main_tag and word_count > 0:
            link_texts = ' '.join(a.get_text(strip=True) for a in main_tag.find_all('a'))
            link_words = len(re.findall(r'\b\w+\b', link_texts))
            link_ratio = round((link_words / word_count) * 100, 1)
            if link_ratio <= 20:
                add_res("Content & E-E-A-T", "CONT-08", "Link Density", "PASS", 0, f"Link text density healthy ({link_ratio}% <= 20%).")
            else:
                add_res("Content & E-E-A-T", "CONT-08", "Link Density", "WARN", -3, f"Link density high ({link_ratio}% > 20%). Risk of directory/hub penalty. Add descriptive body copy.")

        # D. Semantic Landmarks (CIT-12)
        has_main = bool(soup.find('main'))
        has_section = bool(soup.find('section'))
        has_header_footer = bool(soup.find('header') and soup.find('footer'))
        if has_main and (has_section or has_header_footer):
            add_res("AI Citability", "CIT-12", "Semantic Landmarks", "PASS", 0, "Uses semantic HTML5 tags (<main>, <section>, <header>/<footer>).")
        else:
            add_res("AI Citability", "CIT-12", "Semantic Landmarks", "WARN", -2, "Lacks key semantic tags (<main> or <section>). Avoid pure <div> tag nesting.")

        # E. Tables & Lists in Main Content (CIT-07)
        has_table = bool(soup.find('table'))
        has_list = bool(soup.find('ul') or soup.find('ol'))
        if has_table and has_list:
            add_res("AI Citability", "CIT-07", "Structured Tables & Lists", "PASS", 0, "Both <table> and lists (<ul>/<ol>) present for high AI quotation yield.")
        elif has_table or has_list:
            add_res("AI Citability", "CIT-07", "Structured Tables & Lists", "PASS", 0, f"Structured data container present ({'table' if has_table else 'list'}).")
        else:
            add_res("AI Citability", "CIT-07", "Structured Tables & Lists", "FAIL", -6, "0 tables and 0 lists found in main content. AI models struggle to extract structured facts.")

        # F. Statistical Density (CIT-08)
        # Search for metrics like 50MB, 100%, 0 server uploads, 24/7, sub-100ms, 4 formats
        stat_patterns = re.findall(r'\b\d+(?:\.\d+)?\s*(?:%|MB|GB|KB|ms|s|px|x|k|w|fps|sec|times|days|hours|bits|dpi)\b', body_text, re.IGNORECASE)
        stat_count = len(stat_patterns)
        per_500_words = round((stat_count / (word_count or 1)) * 500, 1)
        if per_500_words >= 4:
            add_res("AI Citability", "CIT-08", "Statistical Density", "PASS", 0, f"High statistical density ({stat_count} metrics, {per_500_words} / 500 words).", stat_patterns[:5])
        elif per_500_words >= 1.5:
            add_res("AI Citability", "CIT-08", "Statistical Density", "WARN", -2, f"Moderate statistical density ({stat_count} metrics, {per_500_words} / 500 words). Add precise technical benchmarks.")
        else:
            add_res("AI Citability", "CIT-08", "Statistical Density", "FAIL", -5, f"Low statistical density ({stat_count} metrics). AI citation rates depend on hard quantified parameters.")

        # G. Schema.org & FAQPage Markup (SCH-01, SCH-15, SCH-17)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        if not json_ld_scripts:
            add_res("Schema Markup", "SCH-02", "Structured Data Present", "FAIL", -10, "No JSON-LD structured data detected.")
        else:
            parsed_schemas = []
            syntax_valid = True
            for s in json_ld_scripts:
                try:
                    data = json.loads(s.string or '{}')
                    parsed_schemas.append(data)
                except Exception as e:
                    syntax_valid = False
            
            if not syntax_valid:
                add_res("Schema Markup", "SCH-01", "JSON-LD Syntax", "FAIL", -10, "JSON-LD syntax error (invalid JSON).")
            else:
                add_res("Schema Markup", "SCH-01", "JSON-LD Syntax", "PASS", 0, f"{len(parsed_schemas)} valid JSON-LD block(s) detected.")

            # Flatten types
            types_found = set()
            faq_found = False
            faq_questions = []

            def extract_types(obj):
                nonlocal faq_found
                if isinstance(obj, dict):
                    t = obj.get('@type')
                    if t:
                        if isinstance(t, list):
                            types_found.update(t)
                        else:
                            types_found.add(t)
                        if t == 'FAQPage' or (isinstance(t, list) and 'FAQPage' in t):
                            faq_found = True
                            for entity in obj.get('mainEntity', []):
                                if isinstance(entity, dict) and entity.get('name'):
                                    faq_questions.append(entity.get('name'))
                    for v in obj.values():
                        extract_types(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_types(item)

            for schema in parsed_schemas:
                extract_types(schema)

            has_faq_content = bool(re.search(r'FAQ|Common Questions|Frequently Asked', body_text, re.IGNORECASE))
            if has_faq_content:
                if faq_found:
                    add_res("Schema Markup", "SCH-17", "FAQPage Schema", "PASS", 0, f"FAQPage schema active with {len(faq_questions)} questions.", faq_questions)
                else:
                    add_res("Schema Markup", "SCH-17", "FAQPage Schema", "FAIL", -8, "FAQ section found in content, but FAQPage JSON-LD schema is absent.")
            else:
                if faq_found:
                    add_res("Schema Markup", "SCH-17", "FAQPage Schema", "PASS", 0, "FAQPage schema present.")

    # Calculate overall score
    base_score = 100
    for r in results:
        base_score += r["score_impact"]
    final_score = max(0, min(100, base_score))

    return {
        "score": final_score,
        "results": results
    }

def audit_robots_txt(robots_content):
    checks = []
    lines = [line.strip() for line in robots_content.splitlines() if line.strip() and not line.strip().startswith('#')]
    content_lower = robots_content.lower()
    
    # AI search crawlers to check
    search_bots = ["oai-searchbot", "perplexitybot", "claude-searchbot", "chatgpt-user"]
    for bot in search_bots:
        # Check if disallowed
        pattern = rf'user-agent:\s*{bot}\s+disallow:\s*/'
        if re.search(pattern, content_lower):
            checks.append({"crawler": bot, "status": "FAIL", "message": f"Critical AI search crawler {bot} is blocked from site root."})
        else:
            checks.append({"crawler": bot, "status": "PASS", "message": f"AI search crawler {bot} allowed."})
            
    # Check sitemap reference
    has_sitemap = any(l.lower().startswith('sitemap:') for l in lines)
    return {"sitemap_declared": has_sitemap, "crawler_checks": checks}

def audit_llms_txt(llms_content):
    lines = [l.strip() for l in llms_content.splitlines() if l.strip()]
    non_empty = len(lines)
    # Check markdown links [Text](url)
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', llms_content)
    
    status = "PASS"
    messages = []
    if non_empty < 5:
        status = "FAIL"
        messages.append(f"llms.txt too short ({non_empty} lines, minimum 5 required).")
    if len(links) < 1:
        status = "FAIL"
        messages.append("0 Markdown resource links found. Add at least one [Title](URL) reference.")
    else:
        messages.append(f"Contains {len(links)} linked resource(s).")

    return {
        "status": status,
        "non_empty_lines": non_empty,
        "links_count": len(links),
        "messages": messages
    }

def main():
    parser = argparse.ArgumentParser(description="Audit HTML for Google SEO and GEO (AI Citability) Compliance.")
    parser.add_argument("-f", "--file", help="Path to local HTML file to audit.")
    parser.add_argument("-k", "--keyword", help="Target primary keyword.")
    parser.add_argument("--robots", help="Path to robots.txt to audit.")
    parser.add_argument("--llms", help="Path to llms.txt to audit.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    parser.add_argument(
        "--keyword-only",
        action="store_true",
        help="Run only the keyword-targeting checks (no BeautifulSoup required).",
    )

    args = parser.parse_args()

    if args.keyword_only:
        if not args.file or not args.keyword:
            print("Error: --keyword-only requires --file and --keyword.", file=sys.stderr)
            return 2
        html_path = Path(args.file)
        if not html_path.exists():
            print(f"Error: File {args.file} not found.", file=sys.stderr)
            return 2
        html_content = html_path.read_text(encoding="utf-8", errors="replace")
        checks = audit_keyword_targeting(html_content, args.keyword)
        if args.json:
            print(json.dumps({"keyword_targeting": checks}, indent=2, ensure_ascii=False))
        else:
            for check in checks:
                print(f"[{check['status']:<4}] {check['id']} {check['message']}")
        return 0

    report = {}

    if args.file:
        html_path = Path(args.file)
        if not html_path.exists():
            print(f"Error: File {args.file} not found.", file=sys.stderr)
            sys.exit(1)
        html_content = html_path.read_text(encoding='utf-8')
        report["html_audit"] = audit_html(html_content, target_keyword=args.keyword, check_geo=True)

    if args.robots:
        r_path = Path(args.robots)
        if r_path.exists():
            report["robots_audit"] = audit_robots_txt(r_path.read_text(encoding='utf-8'))

    if args.llms:
        l_path = Path(args.llms)
        if l_path.exists():
            report["llms_audit"] = audit_llms_txt(l_path.read_text(encoding='utf-8'))

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    # Formatted CLI Output
    if "html_audit" in report:
        audit = report["html_audit"]
        score = audit["score"]
        color_tag = "EXCELLENT" if score >= 85 else ("GOOD" if score >= 70 else "NEEDS WORK")
        print("\n" + "="*70)
        print(f"  Google SEO & GEO Audit Score: {score}/100 [{color_tag}]")
        print("="*70)

        for res in audit["results"]:
            icon = "✓ PASS" if res["status"] == "PASS" else ("! WARN" if res["status"] == "WARN" else "✗ FAIL")
            prefix = f"[{icon:6}] ({res['category']}) {res['name']}"
            print(f"{prefix:<50} | {res['message']}")
            if res.get('evidence'):
                print(f"       -> Evidence: {str(res['evidence'])[:100]}")

    if "robots_audit" in report:
        print("\n" + "-"*70)
        print("  robots.txt AI Crawler Governance")
        print("-"*70)
        r = report["robots_audit"]
        print(f"  Sitemap declared: {'YES' if r['sitemap_declared'] else 'NO (Missing)'}")
        for c in r["crawler_checks"]:
            icon = "✓" if c["status"] == "PASS" else "✗"
            print(f"  [{icon}] {c['crawler']:<20} : {c['message']}")

    if "llms_audit" in report:
        print("\n" + "-"*70)
        print("  llms.txt AI Agent Indexing Quality")
        print("-"*70)
        l = report["llms_audit"]
        icon = "✓" if l["status"] == "PASS" else "✗"
        print(f"  [{icon}] Status: {l['status']} (Lines: {l['non_empty_lines']}, Links: {l['links_count']})")
        for m in l["messages"]:
            print(f"       - {m}")
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    raise SystemExit(main())
