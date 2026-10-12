# -*- coding: utf-8 -*-
"""Validate enrichment links: drop dead URLs (404/410/DNS failure), keep the rest.
Usage: py -I -X utf8 scripts/check_links.py <enrich_dir> <out_dir>
"""
import sys, os, json, glob, requests
from concurrent.futures import ThreadPoolExecutor

src, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
      "Accept-Language": "zh-TW,zh;q=0.9"}
DEAD = {404, 410}

def check(url):
    try:
        r = requests.get(url, headers=UA, timeout=20, allow_redirects=True, stream=True)
        code = r.status_code; r.close()
        return code
    except Exception as e:
        return 0

files = sorted(glob.glob(os.path.join(src, "enrich_part*.json")))
all_links = []
for f in files:
    data = json.load(open(f, encoding="utf-8"))
    for e in data:
        for l in e.get("links", []): all_links.append(l)
urls = sorted({l["url"] for l in all_links})
print("checking", len(urls), "urls")
with ThreadPoolExecutor(8) as ex:
    status = dict(zip(urls, ex.map(check, urls)))
kept = dropped = 0
for f in files:
    data = json.load(open(f, encoding="utf-8"))
    for e in data:
        new = []
        for l in e.get("links", []):
            code = status.get(l["url"], 0)
            l["http_status"] = code
            if code in DEAD or code == 0:
                dropped += 1; print("  DROP", code, e.get("name"), l["url"])
            else:
                kept += 1; new.append(l)
        e["links"] = new
    json.dump(data, open(os.path.join(out, os.path.basename(f)), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("kept", kept, "dropped", dropped)
