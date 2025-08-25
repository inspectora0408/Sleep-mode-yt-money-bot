# scripts/generate_posts.py
import os
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

# ---------- CONFIG ----------
REPO_ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = REPO_ROOT / "_posts"
AFF_FILE = REPO_ROOT / "affiliates.json"
# ----------------------------

def load_affiliates():
    if AFF_FILE.exists():
        return json.loads(AFF_FILE.read_text(encoding="utf-8"))
    return {"amazon_tag": "", "amazon_country": "com", "fallback_links": []}

def affiliate_links(query, aff):
    q = quote_plus(query)
    links = []
    if aff.get("amazon_tag"):
        links.append(
            f"https://www.amazon.{aff.get('amazon_country','com')}/s?k={q}&tag={aff['amazon_tag']}"
        )
    for l in aff.get("fallback_links", []):
        links.append(l.format(query=q))

    # de-duplicate while preserving order
    seen, uniq = set(), []
    for url in links:
        if url not in seen:
            seen.add(url)
            uniq.append(url)
    return uniq[:5]

def fetch_trends():
    """
    Robust Google Trends fetch with a safe fallback.
    If pytrends or the network fails, we still return evergreen topics
    so the workflow never fails.
    """
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-US", tz=360)
        df = pytrends.trending_searches(pn="united_states")
        topics = [str(x) for x in df[0].tolist()]
        if topics:
            return topics[:5]
    except Exception as e:
        print("Trends error:", e)

    # Fallback evergreen topics (still monetizable)
    return [
        "best wireless earbuds",
        "home office desk",
        "air fryer recipes",
        "portable power station",
        "budget gaming laptop",
    ]

def slugify(title):
    s = title.lower()
    for ch in ["&","/","?",":","#","'","\"",",",".","(",")","[","]"]:
        s = s.replace(ch, "")
    return "-".join(s.split())[:60] or "trend"

def make_post(topic, aff):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    slug = slugify(topic)
    fname = f"{today}-{slug}.md"
    path = POSTS_DIR / fname

    links = affiliate_links(topic, aff)
    link_md = "\n".join([f"- [{i+1}]({url})" for i, url in enumerate(links)])

    body = f"""---
layout: post
title: "{topic}: Why It's Trending and Where to Buy"
date: {today} 00:00:00 +0000
tags: [trending, {slug}]
---

TL;DR: "{topic}" is trending today. Here is a quick explainer plus helpful links.

## What is "{topic}"?
Currently seeing a surge in searches — usually due to news, viral clips, or launches.

## Why trending
- Google Trends spike
- Social media buzz
- News or product events

## Helpful links (affiliate)
{link_md}

---
Disclosure: Some links may be affiliate links.
"""
    path.write_text(body, encoding="utf-8")
    return path

def main():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    aff = load_affiliates()
    topics = fetch_trends()
    per_run = int(os.getenv("POSTS_PER_RUN", "2"))
    for t in topics[:per_run]:
        make_post(t, aff)

if __name__ == "__main__":
    main()
