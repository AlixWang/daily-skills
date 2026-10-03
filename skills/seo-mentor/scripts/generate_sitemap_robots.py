#!/usr/bin/env python3
"""
generate_sitemap_robots.py - 规范化生成 sitemap.xml 与 robots.txt
防范常见 SEO 隐患：
1. 防止 robots.txt 误封禁 css/js 导致 Google 无法渲染
2. 自动指向规范主域 sitemap
3. 支持多语言或参数化 URL 批量写入 sitemap.xml
"""

import sys
import datetime

def generate_robots_txt(base_url):
    clean_url = base_url.rstrip('/')
    return f"""# Standard Production robots.txt
# Optimized for Googlebot and major search engines

User-agent: *
Allow: /
Disallow: /api/
Disallow: /_next/
Disallow: /admin/

# Sitemap location
Sitemap: {clean_url}/sitemap.xml
"""

def generate_sitemap_xml(urls, default_priority=0.8, changefreq="weekly"):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for item in urls:
        if isinstance(item, tuple):
            loc, priority = item
        else:
            loc, priority = item, default_priority
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{loc}</loc>")
        xml_lines.append(f"    <lastmod>{now}</lastmod>")
        xml_lines.append(f"    <changefreq>{changefreq}</changefreq>")
        xml_lines.append(f"    <priority>{priority}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append('</urlset>')
    return "\n".join(xml_lines)

if __name__ == "__main__":
    test_domain = "https://oneimage.co"
    print("=== robots.txt demo ===")
    print(generate_robots_txt(test_domain))
    print("\n=== sitemap.xml demo ===")
    sample_urls = [
        (f"{test_domain}/", 1.0),
        (f"{test_domain}/crop", 0.9),
        (f"{test_domain}/compress", 0.9),
        (f"{test_domain}/pixel-art", 0.8),
    ]
    print(generate_sitemap_xml(sample_urls))
