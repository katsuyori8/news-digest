#!/usr/bin/env python3
"""BBC News の RSS を取得して news.json を作る（標準ライブラリのみ）。
環境変数 ANTHROPIC_API_KEY があれば、新着分の見出し・概要を日本語に翻訳して title_ja / desc_ja に入れる。"""
import json, os, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape

BASE = "https://feeds.bbci.com"
TOP = "/news/rss.xml"
FEEDS = [("world", "/news/world/rss.xml"), ("uk", "/news/uk/rss.xml"), ("biz", "/news/business/rss.xml"),
         ("tech", "/news/technology/rss.xml"), ("sci", "/news/science_and_environment/rss.xml"),
         ("sport", "/sport/rss.xml"), ("cul", "/news/entertainment_and_arts/rss.xml")]
PER_CAT, OUT = 12, "news.json"

def get(url, data=None, headers=None, timeout=30):
    h = {"User-Agent": "news-digest/1.0 (+https://github.com/katsuyori8)"}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as r:
        return r.read()

def parse(path):
    out = []
    for it in ET.fromstring(get(BASE + path)).iter("item"):
        link = (it.findtext("link") or "").split("?")[0].strip()
        title = unescape((it.findtext("title") or "").strip())
        desc = unescape(re.sub(r"<[^>]+>", "", it.findtext("description") or "")).strip()
        try:
            t = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc).isoformat()
        except Exception:
            t = ""
        if link and title:
            out.append({"title": title, "desc": desc, "link": link, "time": t})
    return out

def translate(items):
    key = os.environ.get("ANTHROPIC_API_KEY")
    todo = [r for r in items if "title_ja" not in r][:40]
    if not key or not todo:
        return
    src = [{"i": i, "t": r["title"], "d": r["desc"]} for i, r in enumerate(todo)]
    prompt = ('次のニュースの見出し(t)と概要(d)を自然な日本語に翻訳し、JSON配列のみで返してください。'
              '各要素は {"i":番号,"t":見出し,"d":概要}。\n' + json.dumps(src, ensure_ascii=False))
    body = json.dumps({"model": os.environ.get("TRANSLATE_MODEL", "claude-haiku-5-5"), "max_tokens": 12000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    try:
        res = json.loads(get("https://api.anthropic.com/v1/messages", body,
                             {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}, 120))
        text = "".join(b.get("text", "") for b in res["content"])
        for a in json.loads(text[text.index("["):text.rindex("]") + 1]):
            todo[a["i"]]["title_ja"], todo[a["i"]]["desc_ja"] = a["t"], a["d"]
    except Exception as e:
        print("translate failed:", e, file=sys.stderr)

def main():
    old = {}
    try:
        old = {d["link"]: d for d in json.load(open(OUT, encoding="utf-8")).get("items", [])}
    except Exception:
        pass
    try:
        top_rows = parse(TOP)[:10]
    except Exception as e:
        top_rows = []
        print("top failed:", e, file=sys.stderr)
    top = {r["link"] for r in top_rows}
    items, seen = [], set()
    for cat, path in FEEDS:
        try:
            rows = parse(path)[:PER_CAT]
        except Exception as e:
            print(cat, "failed:", e, file=sys.stderr)
            continue
        for r in rows:
            if r["link"] not in seen:
                seen.add(r["link"])
                items.append(dict(r, cat=cat, top=r["link"] in top))
    for r in top_rows:
        if r["link"] not in seen:
            seen.add(r["link"])
            items.append(dict(r, cat="world", top=True))
    if not items:
        sys.exit("no items fetched; keeping existing news.json")
    for r in items:
        o = old.get(r["link"])
        if o and o.get("title") == r["title"] and "title_ja" in o:
            r["title_ja"], r["desc_ja"] = o["title_ja"], o.get("desc_ja", "")
    translate(items)
    items.sort(key=lambda r: r["time"], reverse=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now(timezone.utc).isoformat(), "items": items}, f, ensure_ascii=False, indent=1)
    print("wrote", len(items), "items")

if __name__ == "__main__":
    main()
