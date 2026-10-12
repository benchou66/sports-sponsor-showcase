# -*- coding: utf-8 -*-
"""Scrape sponsor.sports.gov.tw athlete/team pages into JSON + download images.
Usage: py -I scripts/scrape.py <listing.html> <out_dir> <raw_detail_dir> <raw_img_dir>
"""
import sys, os, re, json, time, html, urllib.parse
import requests
from bs4 import BeautifulSoup

BASE = "https://sponsor.sports.gov.tw"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
listing_path, out_dir, raw_detail, raw_img = sys.argv[1:5]
os.makedirs(out_dir, exist_ok=True); os.makedirs(raw_detail, exist_ok=True); os.makedirs(raw_img, exist_ok=True)

S = requests.Session(); S.headers["User-Agent"] = UA
DELAY = 0.25

def get(url, dest=None, binary=False):
    for attempt in range(3):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200:
                if dest:
                    with open(dest, "wb") as f: f.write(r.content)
                time.sleep(DELAY)
                return r.content if binary else r.text
            print("  ** HTTP", r.status_code, url, flush=True)
        except Exception as e:
            print("  ** ERR", e, url, flush=True)
        time.sleep(1.5)
    return None

def clean_lines(text):
    lines = [re.sub(r"[ \t　]+", " ", l).strip() for l in text.split("\n")]
    out = []
    for l in lines:
        if l == "" and (not out or out[-1] == ""): continue
        out.append(l)
    return "\n".join(out).strip()

def text_br(el):
    if el is None: return ""
    for br in el.find_all("br"): br.replace_with("\n")
    return clean_lines(el.get_text())

def abs_url(src):
    src = html.unescape(src or "").strip()
    if not src: return ""
    if src.startswith("http"): return src
    src = re.sub(r"^(\.\./)+", "/", src)
    if not src.startswith("/"): src = "/" + src
    return BASE + urllib.parse.quote(src, safe="/:%?=&")

def section_by_title(soup, title):
    for h in soup.select("h2.main-title"):
        if h.get_text(strip=True) == title:
            return h.find_parent("section") or h.parent
    return None

def kv_rows(ul):
    rows = []
    if ul is None: return rows
    for li in ul.select("li"):
        cols = li.select(".row > div")
        if len(cols) >= 2:
            rows.append([cols[0].get_text(" ", strip=True), text_br(cols[1])])
    return rows

def parse_story(doc):
    soup = BeautifulSoup(doc, "lxml")
    d = {}
    hero = soup.select_one(".page-athlete-detail")
    cover = hero.select_one("img.w-100") if hero else None
    d["cover"] = abs_url(cover["src"]) if cover else ""
    nm = soup.select_one("p.fs-1")
    d["name"] = nm.get_text(strip=True) if nm else ""
    amt = soup.select_one("span.fs-2.fs-nst700")
    d["amount_text"] = amt.get_text(strip=True) if amt else ""
    d["amount"] = int(re.sub(r"[^\d]", "", d["amount_text"]) or 0)
    pct = soup.select_one(".money-bar .percentage")
    m = re.search(r"width:\s*([\d.]+)%", pct.get("style", "")) if pct else None
    d["progress_pct"] = float(m.group(1)) if m else 0.0
    first_cl = hero.select_one(".check-list") if hero else None
    d["need_flags"] = [c.get_text(strip=True) for c in first_cl.select(".check span")] if first_cl else []

    sec = section_by_title(soup, "我的故事")
    d["story_title"], d["story"], d["story_images"] = "", "", []
    if sec:
        t = sec.select_one(".template p.fs-4"); d["story_title"] = t.get_text(strip=True) if t else ""
        d["story"] = text_br(sec.select_one(".template p.fs-lg"))
        d["story_images"] = [abs_url(i["src"]) for i in sec.select(".template img")]
    sec = section_by_title(soup, "歷屆成績")
    d["achievements"], d["achievements_updated"] = [], ""
    if sec:
        d["achievements"] = [li.get_text(" ", strip=True) for li in sec.select("#divHisScore li")]
        g = sec.select_one("p.text-gray")
        if g:
            m = re.search(r"(\d{4}/\d{2}/\d{2})", g.get_text()); d["achievements_updated"] = m.group(1) if m else ""
    sec = section_by_title(soup, "推薦理由")
    d["recommendation"] = text_br(sec.select_one("p")) if sec else ""
    sec = section_by_title(soup, "相關照片")
    d["photos"] = [abs_url(i["src"]) for i in sec.select(".photos img")] if sec else []
    sec = section_by_title(soup, "相關影片")
    d["videos"] = []
    if sec:
        cols = sec.select(".row > div")
        i = 0
        while i < len(cols):
            fr = cols[i].select_one("iframe")
            if fr:
                cap = ""
                if i + 1 < len(cols) and not cols[i+1].select_one("iframe"):
                    cap = cols[i+1].get_text(" ", strip=True); i += 1
                d["videos"].append({"url": fr.get("src", ""), "title": cap})
            i += 1
    sec = section_by_title(soup, "相關連結")
    d["links"] = [{"url": a.get("href", ""), "text": a.get_text(" ", strip=True)} for a in sec.select(".links a")] if sec else []
    ul = soup.select_one("ul.title-data")
    d["info"] = kv_rows(ul)
    return d

def parse_plan(doc):
    soup = BeautifulSoup(doc, "lxml"); d = {}
    sec = section_by_title(soup, "關於計畫")
    d["plan_title"], d["plan"], d["plan_images"] = "", "", []
    if sec:
        t = sec.select_one(".template p.fs-4"); d["plan_title"] = t.get_text(strip=True) if t else ""
        d["plan"] = text_br(sec.select_one(".template p.fs-lg"))
        d["plan_images"] = [abs_url(i["src"]) for i in sec.select(".template img")]
    sec = section_by_title(soup, "預期效益")
    d["benefits"] = text_br(sec.select_one("p")) if sec else ""
    return d

def parse_needs(doc):
    soup = BeautifulSoup(doc, "lxml"); d = {}
    sec = section_by_title(soup, "我想達到...")
    d["goals"] = [li.get_text(" ", strip=True) for li in sec.select(".list li")] if sec else []
    sec = section_by_title(soup, "我這樣訓練...")
    d["training_periods"], d["training_methods"] = [], []
    if sec:
        blocks = sec.select(".bg-primary")
        for b in blocks:
            head = b.select_one("p.fs-lg.fs-nst700")
            ht = head.get_text(strip=True) if head else ""
            if "週期" in ht:
                for card in b.select(".h-100"):
                    t = card.select_one("p.fs-5"); body = card.select_one("div")
                    d["training_periods"].append({"title": t.get_text(strip=True) if t else "", "body": text_br(body)})
            else:
                for item in b.select(":scope > div"):
                    ps = item.select("p")
                    if len(ps) >= 2:
                        d["training_methods"].append({"title": ps[0].get_text(strip=True), "body": text_br(ps[1])})
    sec = section_by_title(soup, "所以我需要...")
    d["needs"] = []
    if sec:
        cat = ""
        for tr in sec.select("tbody tr"):
            tds = tr.select("td")
            if len(tds) == 3:
                cat = tds[0].get_text(strip=True); item, qty = tds[1], tds[2]
            elif len(tds) == 2:
                item, qty = tds
            else:
                continue
            d["needs"].append({"category": cat, "item": item.get_text(" ", strip=True), "qty": qty.get_text(" ", strip=True)})
    sec = section_by_title(soup, "聯絡人資訊")
    d["contact"] = kv_rows(sec.select_one("ul.title-data")) if sec else []
    return d

def fname_from_url(u):
    return urllib.parse.unquote(u.rsplit("/", 1)[-1])

# ---- listing
lst = BeautifulSoup(open(listing_path, encoding="utf-8").read(), "lxml")
cards = []
for a in lst.select("a.athlete-box"):
    href = a["href"]  # keep the raw href (token already URL-encoded by the site)
    m_id = re.search(r"sponsorApplyId=(\d+)", href)
    m_tok = re.search(r"paramToken=([^&#]+)", href)
    sid = m_id.group(1); token = m_tok.group(1) if m_tok else ""
    tags = [s.get_text(strip=True) for s in a.select(".tag-primary, .tag-outline-primary")]
    cards.append({
        "id": int(sid), "token": token,
        "name": a.select_one("h2").get_text(strip=True),
        "type": tags[0] if tags else "", "sport": tags[1] if len(tags) > 1 else "",
        "cover_list": abs_url(a.select_one(".cover img")["src"]),
        "need_flags_list": [s.get_text(strip=True) for s in a.select(".check span")],
        "order": len(cards),
    })
print("cards:", len(cards), flush=True)

results = []
for c in cards:
    sid, tok = c["id"], c["token"]  # token is already URL-encoded on the site
    print(f"[{c['order']+1}/{len(cards)}] {sid} {c['name']}", flush=True)
    pages = {}
    for kind, path in (("story", "ApplyDetailStory"), ("plan", "ApplyDetailPlan"), ("needs", "ApplyDetailNeeds")):
        url = f"{BASE}/Home/{path}?sponsorApplyId={sid}&paramToken={tok}"
        dest = os.path.join(raw_detail, f"{sid}_{kind}.html")
        if os.path.exists(dest) and os.path.getsize(dest) > 5000:
            pages[kind] = open(dest, encoding="utf-8", errors="replace").read()
        else:
            txt = get(url, dest)
            pages[kind] = txt or ""
    rec = dict(c)
    rec["source_url"] = f"{BASE}/Home/ApplyDetailStory?sponsorApplyId={sid}&paramToken={tok}"
    rec.update(parse_story(pages["story"]) if pages["story"] else {})
    rec.update(parse_plan(pages["plan"]) if pages["plan"] else {})
    rec.update(parse_needs(pages["needs"]) if pages["needs"] else {})
    # images
    imgs = []
    def add(u, role):
        if u and u not in [i["url"] for i in imgs]: imgs.append({"url": u, "role": role})
    add(rec.get("cover") or c["cover_list"], "cover")
    for u in rec.get("story_images", []): add(u, "story")
    for u in rec.get("plan_images", []): add(u, "plan")
    for u in rec.get("photos", []): add(u, "photo")
    idir = os.path.join(raw_img, str(sid)); os.makedirs(idir, exist_ok=True)
    for im in imgs:
        fn = fname_from_url(im["url"]); dest = os.path.join(idir, fn)
        im["file"] = f"{sid}/{fn}"
        if not (os.path.exists(dest) and os.path.getsize(dest) > 0):
            data = get(im["url"], dest, binary=True)
            if data is None: im["file"] = ""
    rec["images"] = imgs
    results.append(rec)
    with open(os.path.join(out_dir, "sponsor_data.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
print("DONE", len(results), flush=True)
