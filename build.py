#!/usr/bin/env python3
import os
import re
import shutil
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
ARTICLES_DIR = ROOT / "articles"
TEMPLATES_DIR = ROOT / "templates"
OUT_DIR = ROOT / "builds"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml'])
)

article_tpl = env.get_template("article.html")
hub_tpl = env.get_template("hub.html")

FRONT_MATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

def parse_md(file_path):
    text = file_path.read_text(encoding="utf-8")
    m = FRONT_MATTER_REGEX.match(text)
    if not m:
        raise ValueError(f"Missing front-matter in {file_path}")
    meta_raw, body_md = m.group(1), m.group(2)
    meta = yaml.safe_load(meta_raw)
    return meta or {}, body_md

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\-]+', '-', s)
    s = re.sub(r'\-+', '-', s)
    return s.strip('-')

def ensure_out():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "brand").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "topic").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "country").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "articles").mkdir(parents=True, exist_ok=True)

def to_html(md_text):
    return markdown.markdown(md_text, extensions=['fenced_code', 'codehilite', 'tables'])

def build():
    ensure_out()
    index = []
    # read all articles
    for mdfile in ARTICLES_DIR.glob("*.md"):
        meta, body_md = parse_md(mdfile)
        title = meta.get("title") or "Untitled"
        slug = meta.get("slug") or slugify(title)
        brand = meta.get("brand")
        series = meta.get("series")
        topics = meta.get("topics") or []
        countries = meta.get("countries") or []
        date = meta.get("date")
        summary = meta.get("summary") or ""
        content_html = to_html(body_md)

        url = f"/articles/{slug}.html"
        article_obj = {
            "title": title,
            "slug": slug,
            "url": url,
            "brand": brand,
            "series": series,
            "topics": topics,
            "countries": countries,
            "date": date,
            "summary": summary,
            "content_html": content_html,
            "meta": meta
        }
        index.append(article_obj)

    # build lookup maps
    brands = {}
    brand_series = {}
    topics_map = {}
    countries_map = {}
    for a in index:
        # brand hub
        if a["brand"]:
            brands.setdefault(a["brand"], []).append(a)
        # brand-series hub
        if a["brand"] and a["series"]:
            key = f"{a['brand']}-{a['series']}"
            brand_series.setdefault(key, []).append(a)
        # topics
        for t in a["topics"]:
            topics_map.setdefault(t, []).append(a)
        # countries
        for c in a["countries"]:
            countries_map.setdefault(c, []).append(a)

    # write article pages
    for a in index:
        out_path = OUT_DIR / "articles" / f"{a['slug']}.html"
        rendered = article_tpl.render(
            title=a['title'],
            date=a.get('date'),
            brand=a.get('brand'),
            series=a.get('series'),
            summary=a.get('summary'),
            content_html=a['content_html'],
            related={
                "brand": bool(a.get('brand')),
                "series": bool(a.get('series')),
                "topics": a.get('topics'),
                "countries": a.get('countries')
            },
            meta=a
        )
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote article: {out_path}")

    # write brand hubs
    for b, items in brands.items():
        out_path = OUT_DIR / "brand" / f"{b}.html"
        items_sorted = sorted(items, key=lambda x: x.get("date") or "", reverse=True)
        rendered = hub_tpl.render(hub_title=f"Brand: {b}", hub_desc=None, items=[{"title": it['title'], "url": it['url'], "summary": it.get('summary')} for it in items_sorted])
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote brand hub: {out_path}")

    # write brand-series hubs
    for key, items in brand_series.items():
        out_path = OUT_DIR / "brand" / f"{key}.html"
        rendered = hub_tpl.render(hub_title=f"Series: {key}", hub_desc=None, items=[{"title": it['title'], "url": it['url'], "summary": it.get('summary')} for it in items])
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote brand-series hub: {out_path}")

    # write topic hubs
    for t, items in topics_map.items():
        out_path = OUT_DIR / "topic" / f"{t}.html"
        rendered = hub_tpl.render(hub_title=f"Topic: {t}", hub_desc=None, items=[{"title": it['title'], "url": it['url'], "summary": it.get('summary')} for it in items])
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote topic hub: {out_path}")

    # write country hubs
    for c, items in countries_map.items():
        out_path = OUT_DIR / "country" / f"{c}.html"
        rendered = hub_tpl.render(hub_title=f"Country: {c}", hub_desc=None, items=[{"title": it['title'], "url": it['url'], "summary": it.get('summary')} for it in items])
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote country hub: {out_path}")

    # write a simple index page
    index_page = OUT_DIR / "index.html"
    all_items = sorted(index, key=lambda x: x.get("date") or "", reverse=True)
    rendered_index = hub_tpl.render(hub_title="Index", hub_desc="Latest articles", items=[{"title": it['title'], "url": it['url'], "summary": it.get('summary')} for it in all_items])
    index_page.write_text(rendered_index, encoding="utf-8")
    print(f"Wrote index: {index_page}")

if __name__ == "__main__":
    build()
