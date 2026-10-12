# -*- coding: utf-8 -*-
"""Build the static showcase site from the scraped JSON.
Usage: py -I -X utf8 scripts/build.py <sponsor_data.json> <raw_img_dir> <enrich_dir> <site_out_dir>
"""
import sys, os, re, json, html, glob, random, datetime
from PIL import Image, ImageOps

SRC_JSON, RAW_IMG, ENRICH_DIR, OUT = sys.argv[1:5]
SCRAPE_DATE = "2026-10-12"
SOURCE_SITE = "https://sponsor.sports.gov.tw/"
SOURCE_NAME = "體育署 體育運動捐贈媒合平臺"

os.makedirs(os.path.join(OUT, "p"), exist_ok=True)
os.makedirs(os.path.join(OUT, "img"), exist_ok=True)
os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)

def esc(s): return html.escape(str(s or ""), quote=True)
def money(n): return "NT$ {:,}".format(int(n or 0))
def paras(text):
    text = (text or "").strip()
    if not text: return ""
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for b in blocks:
        b = esc(b.strip()).replace("\n", "<br>")
        if b: out.append(f"<p>{b}</p>")
    return "\n".join(out)
def county_of(s):
    m = re.match(r"^(.{2}[縣市])", s or "")
    return m.group(1) if m else (s or "")
def info_get(rec, key):
    for k, v in rec.get("info", []):
        if k == key: return v
    return ""
def amount_int(s):
    d = re.sub(r"[^\d]", "", s or "")
    return int(d) if d else None

# ---------- images ----------
def optimize(src, dst, max_w, q=82):
    if not os.path.exists(src) or os.path.getsize(src) == 0: return False
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): return True
    try:
        im = Image.open(src); im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB",): im = im.convert("RGB")
        w, h = im.size
        if w > max_w:
            im = im.resize((max_w, round(h * max_w / w)), Image.LANCZOS)
        im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
        return True
    except Exception as e:
        print("  image fail", src, e); return False

# ---------- load ----------
records = json.load(open(SRC_JSON, encoding="utf-8"))
enrich = {}
for f in glob.glob(os.path.join(ENRICH_DIR, "enrich_part*.json")):
    try:
        for e in json.load(open(f, encoding="utf-8")):
            links = [l for l in e.get("links", []) if l.get("url", "").startswith("http")
                     and "sponsor.sports.gov.tw" not in l["url"] and "donate.sports.gov.tw" not in l["url"]]
            if links: enrich[int(e["id"])] = links
    except Exception as ex:
        print("enrich load fail", f, ex)
print("records", len(records), "enriched", len(enrich))

for r in records:
    rid = r["id"]
    r["county"] = county_of(info_get(r, "縣市別"))
    r["region"] = info_get(r, "縣市別")
    r["remote"] = info_get(r, "偏鄉") == "是"
    r["coach"] = info_get(r, "指導教練")
    r["tagline"] = r.get("story_title") or r["name"]
    story = re.sub(r"\s+", " ", r.get("story") or "")
    r["excerpt"] = (story[:72] + "…") if len(story) > 72 else story
    r["flags"] = sorted(set(r.get("need_flags_list") or r.get("need_flags") or []), key=lambda x: x != "經費需求")
    r["achievements"] = [a for a in r.get("achievements", []) if a.strip()]
    r["fund_items"] = [n for n in r.get("needs", []) if n["category"] == "經費需求"]
    r["supply_items"] = [n for n in r.get("needs", []) if n["category"] != "經費需求"]
    r["fund_total"] = sum((amount_int(n["qty"]) or 0) for n in r["fund_items"])
    r["media"] = enrich.get(rid, [])
    # featured score
    s = 0.0
    s += 3 if r.get("videos") else 0
    s += min(len(r.get("story") or ""), 1500) / 500
    s += 0.5 * len(r.get("photos", [])) + 0.5 * len(r.get("story_images", []))
    s += 1.5 if r["remote"] else 0
    s += 1 if r.get("achievements") else 0
    r["score"] = round(s, 2)
    # images
    idir = os.path.join(OUT, "img", str(rid)); os.makedirs(idir, exist_ok=True)
    r["img"] = {"cover": "", "cover_sm": "", "story": [], "plan": [], "photos": []}
    counters = {"story": 0, "plan": 0, "photo": 0}
    for im in r.get("images", []):
        if not im.get("file"): continue
        src = os.path.join(RAW_IMG, im["file"])
        if im["role"] == "cover":
            if optimize(src, os.path.join(idir, "cover.jpg"), 1600): r["img"]["cover"] = f"img/{rid}/cover.jpg"
            if optimize(src, os.path.join(idir, "cover_sm.jpg"), 720, 80): r["img"]["cover_sm"] = f"img/{rid}/cover_sm.jpg"
        else:
            role = im["role"]; counters[role] += 1
            fn = f"{role}-{counters[role]}.jpg"
            if optimize(src, os.path.join(idir, fn), 1400):
                r["img"]["photos" if role == "photo" else role].append(f"img/{rid}/{fn}")
    if not r["img"]["cover"] and r["img"]["photos"]:
        r["img"]["cover"] = r["img"]["photos"][0]; r["img"]["cover_sm"] = r["img"]["photos"][0]

records.sort(key=lambda r: -r["score"])
sports = sorted({r["sport"] for r in records}, key=lambda s: -sum(1 for r in records if r["sport"] == s))
counties = sorted({r["county"] for r in records if r["county"]})
n_ath = sum(1 for r in records if r["type"] == "運動員"); n_team = len(records) - n_ath
total_amount = sum(r.get("amount", 0) for r in records)
n_remote = sum(1 for r in records if r["remote"])

# ---------- CSS ----------
CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&family=Oswald:wght@500;600;700&display=swap');
:root{--bg:#0b1020;--bg2:#121a33;--ink:#141a2b;--paper:#fff;--soft:#f4f6fb;--muted:#667085;--line:#e6e9f2;
--accent:#c9ff3b;--accent-ink:#0b1020;--blue:#2f6bff;--coral:#ff5a3c;--gold:#f5b700;--silver:#9aa4b2;--bronze:#c97d4a;
--radius:18px;--shadow:0 10px 30px rgba(10,16,40,.10);--shadow-lg:0 24px 60px rgba(10,16,40,.18);--max:1200px}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;color:var(--ink);background:var(--paper);line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}img{display:block;max-width:100%}
.num{font-family:Oswald,"Noto Sans TC",sans-serif;font-weight:600;letter-spacing:.01em}
.wrap{max-width:var(--max);margin:0 auto;padding:0 20px}
/* nav */
.nav{position:sticky;top:0;z-index:50;background:rgba(11,16,32,.92);backdrop-filter:saturate(160%) blur(10px);color:#fff;border-bottom:1px solid rgba(255,255,255,.08)}
.nav .wrap{display:flex;align-items:center;gap:22px;height:64px}
.brand{display:flex;align-items:center;gap:10px;font-weight:900;font-size:17px;letter-spacing:.02em}
.brand i{display:inline-block;width:26px;height:26px;border-radius:8px;background:var(--accent);box-shadow:0 0 0 4px rgba(201,255,59,.18)}
.brand small{display:block;font-weight:500;font-size:11px;color:#aab3cc;letter-spacing:.12em}
.nav-links{margin-left:auto;display:flex;gap:18px;font-size:14px;color:#c7cde0}
.nav-links a:hover{color:#fff}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:12px 22px;border-radius:999px;font-weight:700;border:0;cursor:pointer;transition:transform .15s,box-shadow .15s;white-space:nowrap}
.btn:hover{transform:translateY(-1px)}
.btn-accent{background:var(--accent);color:var(--accent-ink);box-shadow:0 8px 24px rgba(201,255,59,.35)}
.btn-ghost{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.25)}
.btn-line{background:#fff;color:var(--ink);border:1.5px solid var(--line)}
.btn-sm{padding:8px 14px;font-size:13px}
/* hero (index) */
.hero{position:relative;background:var(--bg);color:#fff;overflow:hidden;min-height:620px;display:flex;align-items:center}
.hero .mosaic{position:absolute;inset:0;display:grid;grid-template-columns:repeat(6,1fr);grid-auto-rows:1fr;gap:6px;opacity:.55;filter:saturate(1.1)}
.hero .mosaic div{background-size:cover;background-position:center;min-height:200px}
.hero .mosaic div:nth-child(3n){grid-row:span 2}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(11,16,32,.96) 0%,rgba(11,16,32,.9) 38%,rgba(11,16,32,.45) 75%,rgba(11,16,32,.25) 100%)}
.hero .wrap{position:relative;z-index:2;padding-top:80px;padding-bottom:80px}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:13px;letter-spacing:.2em;color:var(--accent);font-weight:700;text-transform:uppercase}
.eyebrow::before{content:"";width:28px;height:2px;background:var(--accent)}
.hero h1{font-size:clamp(34px,5vw,62px);line-height:1.15;margin:18px 0 16px;font-weight:900;letter-spacing:.01em;max-width:760px}
.hero h1 em{font-style:normal;color:var(--accent)}
.hero p.lead{font-size:18px;color:#c7cde0;max-width:620px;margin:0 0 30px}
.stats{display:flex;flex-wrap:wrap;gap:34px;margin-top:40px}
.stat b{display:block;font-size:40px;line-height:1;color:#fff}.stat span{font-size:13px;color:#aab3cc;letter-spacing:.08em}
/* featured */
.section{padding:70px 0}
.section-head{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:28px}
.section-head h2{font-size:30px;margin:0;font-weight:900;letter-spacing:.01em}
.section-head p{margin:6px 0 0;color:var(--muted)}
.featured{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:18px}
.feat{position:relative;border-radius:var(--radius);overflow:hidden;min-height:340px;background:#222 center/cover no-repeat;color:#fff;display:flex;align-items:flex-end;box-shadow:var(--shadow);transition:transform .25s,box-shadow .25s}
.feat:first-child{min-height:520px;grid-row:span 2}
.feat:hover{transform:translateY(-4px);box-shadow:var(--shadow-lg)}
.feat::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 30%,rgba(5,8,20,.92) 100%)}
.feat .in{position:relative;z-index:2;padding:26px}
.feat h3{margin:8px 0 6px;font-size:24px;line-height:1.3}.feat:first-child h3{font-size:32px}
.feat p{margin:0;color:#d7dcea;font-size:14px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.tags{display:flex;flex-wrap:wrap;gap:6px}
.tag{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:700;letter-spacing:.04em;background:rgba(255,255,255,.14);color:#fff;border:1px solid rgba(255,255,255,.18)}
.tag.t-ath{background:var(--accent);color:var(--accent-ink);border-color:transparent}
.tag.t-team{background:var(--blue);color:#fff;border-color:transparent}
.tag.t-remote{background:var(--coral);color:#fff;border-color:transparent}
.card .tag{background:var(--soft);color:var(--ink);border-color:var(--line)}
.card .tag.t-ath{background:#e9ffb0;color:#2d4300}.card .tag.t-team{background:#e3ecff;color:#1b3fa0}.card .tag.t-remote{background:#ffe4de;color:#9a2a14}
/* filters */
.filters{position:sticky;top:64px;z-index:40;background:rgba(255,255,255,.94);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);padding:14px 0}
.filters .wrap{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.seg{display:inline-flex;background:var(--soft);border-radius:999px;padding:4px}
.seg button{border:0;background:transparent;padding:8px 16px;border-radius:999px;font-weight:700;cursor:pointer;color:var(--muted);font-family:inherit}
.seg button.on{background:var(--ink);color:#fff}
.filters select,.filters input{font-family:inherit;font-size:14px;padding:10px 14px;border:1.5px solid var(--line);border-radius:12px;background:#fff;color:var(--ink)}
.filters input{min-width:220px}
.chk{display:inline-flex;align-items:center;gap:6px;font-size:14px;color:var(--muted);font-weight:700}
.count{margin-left:auto;color:var(--muted);font-size:14px}
/* cards */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:22px}
.card{display:flex;flex-direction:column;background:#fff;border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);border:1px solid var(--line);transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-5px);box-shadow:var(--shadow-lg)}
.card .cover{aspect-ratio:4/3;background:#e9ecf5 center/cover no-repeat;position:relative}
.card .cover .pct{position:absolute;right:12px;bottom:12px;background:rgba(11,16,32,.85);color:#fff;font-size:12px;padding:4px 10px;border-radius:999px}
.card .body{padding:16px 18px 18px;display:flex;flex-direction:column;gap:8px;flex:1}
.card h3{margin:4px 0 0;font-size:18px;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{font-size:12.5px;color:var(--muted)}
.card .ex{font-size:13.5px;color:#475467;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin:0}
.card .foot{margin-top:auto;padding-top:12px;border-top:1px dashed var(--line);display:flex;justify-content:space-between;align-items:end}
.card .foot b{font-size:19px}.card .foot small{display:block;font-size:11px;color:var(--muted);letter-spacing:.08em}
.bar{height:6px;background:#eceff6;border-radius:999px;overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),#7ddc3c);border-radius:999px}
.flags{display:flex;gap:6px}.flag{font-size:11px;padding:2px 8px;border-radius:6px;background:var(--soft);color:var(--muted);font-weight:700}
/* sport chips */
.chips{display:flex;flex-wrap:wrap;gap:10px}
.chip{padding:9px 16px;border-radius:999px;border:1.5px solid var(--line);font-weight:700;font-size:14px;cursor:pointer;background:#fff;font-family:inherit}
.chip:hover{border-color:var(--ink)}.chip b{color:var(--muted);font-weight:500;margin-left:4px}
.empty{padding:60px;text-align:center;color:var(--muted)}
/* footer */
.footer{background:var(--bg);color:#aab3cc;padding:50px 0;font-size:13px;margin-top:60px}
.footer a{color:#fff;text-decoration:underline}
/* ---------- detail ---------- */
.dhero{background:var(--bg);color:#fff;padding:46px 0 54px}
.dhero .wrap{display:grid;grid-template-columns:1.25fr 1fr;gap:40px;align-items:center}
.dhero .pic{border-radius:24px;overflow:hidden;box-shadow:var(--shadow-lg);aspect-ratio:4/3;background:#222 center/cover no-repeat}
.dhero h1{font-size:clamp(30px,3.6vw,46px);margin:14px 0 6px;line-height:1.2;font-weight:900}
.dhero .tagline{font-size:17px;color:#c7cde0;margin:0 0 14px}
.dhero .where{font-size:14px;color:#aab3cc;display:flex;gap:14px;flex-wrap:wrap}
.need{margin-top:24px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:18px;padding:20px 22px}
.need .row{display:flex;justify-content:space-between;align-items:end;gap:12px}
.need .row b{font-size:36px;line-height:1}.need .row span{color:#aab3cc;font-size:13px;letter-spacing:.1em}
.need .bar{background:rgba(255,255,255,.12);margin:12px 0 6px;height:8px}
.need .pct{display:flex;justify-content:space-between;font-size:13px;color:#aab3cc}
.cta{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap}
.crumb{font-size:13px;color:#aab3cc;margin-bottom:10px}.crumb a:hover{color:#fff}
.subnav{position:sticky;top:64px;z-index:40;background:rgba(255,255,255,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.subnav .wrap{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none}
.subnav a{padding:16px 14px;font-size:14px;font-weight:700;color:var(--muted);white-space:nowrap;border-bottom:3px solid transparent}
.subnav a.on,.subnav a:hover{color:var(--ink);border-color:var(--accent)}
.dsec{padding:64px 0;border-bottom:1px solid var(--line)}
.dsec:nth-child(even){background:var(--soft)}
.dsec h2{font-size:28px;margin:0 0 6px;font-weight:900;display:flex;align-items:center;gap:12px}
.dsec h2 .no{font-family:Oswald,sans-serif;font-size:14px;color:var(--accent-ink);background:var(--accent);padding:2px 9px;border-radius:8px;letter-spacing:.1em}
.dsec .sub{color:var(--muted);margin:0 0 26px;font-size:14px}
.prose{max-width:820px;font-size:17px;line-height:1.95}
.prose p{margin:0 0 1.1em}
.prose-title{font-size:22px;font-weight:900;margin:0 0 16px;color:var(--ink)}
.storypics{display:grid;gap:14px;margin-top:28px;max-width:960px}
.storypics img{border-radius:16px;box-shadow:var(--shadow);width:100%}
.quote{margin:34px 0 0;padding:22px 26px;border-left:5px solid var(--accent);background:#fff;border-radius:0 16px 16px 0;max-width:820px;box-shadow:var(--shadow)}
.quote h4{margin:0 0 8px;font-size:14px;letter-spacing:.14em;color:var(--muted)}
.ach{list-style:none;padding:0;margin:0;display:grid;gap:10px;max-width:900px}
.ach li{display:flex;gap:14px;align-items:flex-start;background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 18px;font-weight:500}
.ach .medal{flex:0 0 34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;background:var(--soft)}
.ach .medal.g{background:#fff1bf}.ach .medal.s{background:#eceff3}.ach .medal.b{background:#f7dfcf}
.ach .yr{font-family:Oswald,sans-serif;font-size:12px;color:var(--muted);letter-spacing:.1em;margin-right:8px}
.kv{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;max-width:1000px}
.kv div{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.kv small{display:block;font-size:12px;color:var(--muted);letter-spacing:.08em;margin-bottom:4px}
.kv b{font-size:16px;font-weight:700}
h3.sub-h{font-size:18px;margin:40px 0 14px;font-weight:900;display:flex;align-items:center;gap:10px}
h3.sub-h::before{content:"";width:10px;height:10px;border-radius:3px;background:var(--accent)}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.gallery a{display:block;aspect-ratio:4/3;border-radius:14px;overflow:hidden;background:#ddd center/cover no-repeat;box-shadow:var(--shadow);cursor:zoom-in}
.videos{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:18px}
.video{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:var(--shadow)}
.video .fr{aspect-ratio:16/9;background:#000}.video iframe{width:100%;height:100%;border:0}
.video p{margin:0;padding:12px 16px;font-weight:700;font-size:14px}
.links{display:flex;flex-direction:column;gap:8px;max-width:820px}
.links a{display:flex;align-items:center;gap:10px;padding:12px 16px;background:#fff;border:1px solid var(--line);border-radius:12px;font-weight:700}
.links a:hover{border-color:var(--ink)}
.links a small{margin-left:auto;color:var(--muted);font-weight:400;font-size:12px;max-width:50%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.goals{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.goals li{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;font-weight:700}
.goals .n{font-family:Oswald,sans-serif;font-size:22px;color:var(--blue);min-width:28px}
.periods{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.period{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px 24px;box-shadow:var(--shadow)}
.period h4{margin:0 0 12px;font-size:19px;display:flex;align-items:center;gap:10px}
.period h4 i{width:10px;height:10px;border-radius:50%;background:var(--blue);display:inline-block}
.period .t{font-size:14.5px;color:#344054;line-height:1.85}
.methods{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin-top:6px}
.method{background:var(--bg2);color:#fff;border-radius:18px;padding:20px 22px}
.method h4{margin:0 0 10px;font-size:16px;color:var(--accent)}
.method .t{font-size:14px;color:#d7dcea;line-height:1.8}
.needs{max-width:900px;display:grid;grid-template-columns:1fr 1fr;gap:18px}
.needbox{background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:var(--shadow)}
.needbox h4{margin:0;padding:14px 20px;background:var(--ink);color:#fff;font-size:15px;letter-spacing:.06em}
.needbox table{width:100%;border-collapse:collapse}
.needbox td{padding:12px 20px;border-top:1px solid var(--line);font-size:15px}
.needbox td:last-child{text-align:right;font-family:Oswald,sans-serif;font-size:17px;white-space:nowrap}
.needbox tr.total td{background:#f9ffe6;font-weight:900}
.contact{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;max-width:1000px}
.media{display:grid;gap:12px;max-width:900px}
.media a{display:block;background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 20px}
.media a:hover{border-color:var(--ink)}
.media .src{font-size:12px;color:var(--muted);letter-spacing:.06em;display:flex;gap:8px;align-items:center}
.media .src i{display:inline-block;padding:1px 8px;border-radius:6px;background:var(--soft);font-style:normal;font-weight:700;color:var(--ink)}
.media b{display:block;margin:6px 0 4px;font-size:16px}
.media p{margin:0;font-size:14px;color:#475467}
.media .u{font-size:12px;color:var(--blue);word-break:break-all;margin-top:6px;display:block}
.note{font-size:13px;color:var(--muted);margin-top:14px}
.related .grid{grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}
.lb{position:fixed;inset:0;background:rgba(5,8,20,.92);display:none;align-items:center;justify-content:center;z-index:100;cursor:zoom-out}
.lb.on{display:flex}.lb img{max-width:92vw;max-height:90vh;border-radius:10px;box-shadow:var(--shadow-lg)}
.back-top{position:fixed;right:20px;bottom:20px;z-index:60}
@media (max-width:900px){.featured{grid-template-columns:1fr 1fr}.feat:first-child{grid-column:span 2;min-height:360px}.dhero .wrap{grid-template-columns:1fr}.needs{grid-template-columns:1fr}.nav-links{display:none}}
@media (max-width:600px){.featured{grid-template-columns:1fr}.feat:first-child{grid-column:auto}.hero{min-height:520px}.stats{gap:22px}.stat b{font-size:30px}.filters input{min-width:0;flex:1}.section{padding:46px 0}.dsec{padding:44px 0}.prose{font-size:16px}}
"""

JS_INDEX = r"""
(function(){
  const data = JSON.parse(document.getElementById('data').textContent);
  const grid = document.getElementById('grid'); const count = document.getElementById('count');
  const state = {type:'all', sport:'', county:'', remote:false, q:'', sort:'score'};
  function card(r){
    const cover = r.cover ? `style="background-image:url('${r.cover}')"` : '';
    const pct = r.pct ? `<span class="pct">${r.pct}%</span>` : '';
    return `<a class="card" href="p/${r.id}.html">
      <div class="cover" ${cover}>${pct}</div>
      <div class="body">
        <div class="tags"><span class="tag ${r.type==='運動員'?'t-ath':'t-team'}">${r.type}</span><span class="tag">${r.sport}</span>${r.remote?'<span class="tag t-remote">偏鄉</span>':''}</div>
        <h3>${r.name}</h3>
        <div class="meta">${r.county||''}${r.coach?' · 教練 '+r.coach:''}</div>
        <p class="ex">${r.excerpt||''}</p>
        <div class="foot"><div><small>需求金額</small><b class="num">${r.amount_text}</b></div><div class="flags">${r.flags.map(f=>`<span class="flag">${f.replace('需求','')}</span>`).join('')}</div></div>
        <div class="bar"><i style="width:${Math.min(100,r.pct)}%"></i></div>
      </div></a>`;
  }
  function apply(){
    let rows = data.filter(r => (state.type==='all'||r.type===state.type)
      && (!state.sport||r.sport===state.sport) && (!state.county||r.county===state.county)
      && (!state.remote||r.remote) && (!state.q||(r.name+r.sport+r.county+r.tagline+r.excerpt+(r.coach||'')).toLowerCase().includes(state.q)));
    const s = state.sort;
    rows.sort((a,b)=> s==='amount_desc'?b.amount-a.amount : s==='amount_asc'?a.amount-b.amount : s==='name'?a.name.localeCompare(b.name,'zh-Hant') : s==='updated'?(b.updated||'').localeCompare(a.updated||'') : b.score-a.score);
    grid.innerHTML = rows.length ? rows.map(card).join('') : '<div class="empty">找不到符合條件的計畫，試試放寬篩選。</div>';
    count.textContent = `顯示 ${rows.length} / ${data.length} 個計畫`;
    document.querySelectorAll('.seg button').forEach(b=>b.classList.toggle('on', b.dataset.type===state.type));
  }
  document.querySelectorAll('.seg button').forEach(b=>b.addEventListener('click',()=>{state.type=b.dataset.type;apply();}));
  document.getElementById('sport').addEventListener('change',e=>{state.sport=e.target.value;apply();});
  document.getElementById('county').addEventListener('change',e=>{state.county=e.target.value;apply();});
  document.getElementById('remote').addEventListener('change',e=>{state.remote=e.target.checked;apply();});
  document.getElementById('sort').addEventListener('change',e=>{state.sort=e.target.value;apply();});
  document.getElementById('q').addEventListener('input',e=>{state.q=e.target.value.trim().toLowerCase();apply();});
  document.querySelectorAll('.chip[data-sport]').forEach(c=>c.addEventListener('click',()=>{state.sport=c.dataset.sport;document.getElementById('sport').value=state.sport;apply();document.getElementById('browse').scrollIntoView({behavior:'smooth'});}));
  apply();
})();
"""

JS_DETAIL = r"""
(function(){
  const links=[...document.querySelectorAll('.subnav a')]; const secs=links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
  function spy(){ let cur=secs[0]; for(const s of secs){ if(s.getBoundingClientRect().top-140<=0) cur=s; } links.forEach(a=>a.classList.toggle('on', a.getAttribute('href')==='#'+cur.id)); }
  window.addEventListener('scroll',spy,{passive:true}); spy();
  const lb=document.getElementById('lb'), lbi=lb.querySelector('img');
  document.querySelectorAll('[data-full]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();lbi.src=a.dataset.full;lb.classList.add('on');}));
  lb.addEventListener('click',()=>lb.classList.remove('on'));
  const sh=document.getElementById('share'); if(sh) sh.addEventListener('click',()=>{ (navigator.clipboard?navigator.clipboard.writeText(location.href):Promise.reject()).then(()=>{sh.textContent='已複製連結 ✓';setTimeout(()=>sh.textContent='分享此頁',1800);}).catch(()=>prompt('複製此網址',location.href)); });
})();
"""

# ---------- shared fragments ----------
def nav(root=""):
    return f"""<header class="nav"><div class="wrap">
  <a class="brand" href="{root}index.html"><i></i><span>為台灣運動員而跑<small>ATHLETE &amp; TEAM SUPPORT</small></span></a>
  <nav class="nav-links"><a href="{root}index.html#browse">所有計畫</a><a href="{root}index.html#sports">運動種類</a><a href="{SOURCE_SITE}" target="_blank" rel="noopener">官方捐贈平臺 ↗</a></nav>
</div></header>"""

def footer():
    return f"""<footer class="footer"><div class="wrap">
  <p><b style="color:#fff">資料來源</b>：<a href="{SOURCE_SITE}" target="_blank" rel="noopener">{SOURCE_NAME}</a>（公開頁面，擷取日期 {SCRAPE_DATE}）。本站為資料展示重製版，所有故事、照片、影片與聯絡資訊之著作權屬原申請單位／運動員所有；捐贈請至官方平臺進行。</p>
  <p>媒體報導與社群連結為網路公開搜尋結果，均附原始出處連結；如有錯置請以原始頁面為準。</p>
</div></footer>"""

def type_tag(r, card=False):
    cls = "t-ath" if r["type"] == "運動員" else "t-team"
    t = f'<span class="tag {cls}">{esc(r["type"])}</span><span class="tag">{esc(r["sport"])}</span>'
    if r["remote"]: t += '<span class="tag t-remote">偏鄉</span>'
    return f'<div class="tags">{t}</div>'

def card_html(r, root=""):
    cover = f' style="background-image:url(\'{root}{r["img"]["cover_sm"]}\')"' if r["img"]["cover_sm"] else ""
    pct = r.get("progress_pct", 0) or 0
    pct_badge = f'<span class="pct">{pct:g}%</span>' if pct else ""
    flags = "".join(f'<span class="flag">{esc(f.replace("需求",""))}</span>' for f in r["flags"])
    meta = esc(r["county"]) + (f" · 教練 {esc(r['coach'])}" if r["coach"] else "")
    return f"""<a class="card" href="{root}p/{r['id']}.html">
  <div class="cover"{cover}>{pct_badge}</div>
  <div class="body">{type_tag(r, True)}<h3>{esc(r['name'])}</h3><div class="meta">{meta}</div><p class="ex">{esc(r['excerpt'])}</p>
  <div class="foot"><div><small>需求金額</small><b class="num">{money(r.get('amount'))}</b></div><div class="flags">{flags}</div></div>
  <div class="bar"><i style="width:{min(100, pct)}%"></i></div></div></a>"""

# ---------- index ----------
def render_index():
    feats, seen = [], set()
    for r in records:
        if r["sport"] in seen or not r["img"]["cover"]: continue
        feats.append(r); seen.add(r["sport"])
        if len(feats) == 3: break
    mosaic_pool = [r for r in records if r["img"]["cover_sm"]]
    random.seed(7); mosaic = random.sample(mosaic_pool, min(12, len(mosaic_pool)))
    mosaic_html = "".join(f'<div style="background-image:url(\'{r["img"]["cover_sm"]}\')"></div>' for r in mosaic)
    feat_html = ""
    for r in feats:
        feat_html += f"""<a class="feat" href="p/{r['id']}.html" style="background-image:url('{r['img']['cover']}')"><div class="in">{type_tag(r)}<h3>{esc(r['name'])}</h3><p>{esc(r['tagline'] if r['tagline']!=r['name'] else r['excerpt'])}</p></div></a>"""
    sport_opts = "".join(f'<option value="{esc(s)}">{esc(s)}（{sum(1 for r in records if r["sport"]==s)}）</option>' for s in sports)
    county_opts = "".join(f'<option value="{esc(c)}">{esc(c)}（{sum(1 for r in records if r["county"]==c)}）</option>' for c in counties)
    chips = "".join(f'<button class="chip" data-sport="{esc(s)}">{esc(s)}<b>{sum(1 for r in records if r["sport"]==s)}</b></button>' for s in sports)
    data = [{"id": r["id"], "name": r["name"], "type": r["type"], "sport": r["sport"], "county": r["county"], "remote": r["remote"],
             "coach": r["coach"], "amount": r.get("amount", 0), "amount_text": money(r.get("amount")), "pct": r.get("progress_pct", 0) or 0,
             "flags": r["flags"], "excerpt": r["excerpt"], "tagline": r["tagline"], "cover": r["img"]["cover_sm"], "score": r["score"],
             "updated": r.get("achievements_updated", "")} for r in records]
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>為台灣運動員而跑｜{len(records)} 個等待支持的運動員與團隊</title>
<meta name="description" content="整理自{SOURCE_NAME}的 {n_ath} 位運動員與 {n_team} 支運動團隊：他們的故事、成績、訓練計畫與捐贈需求，一頁看懂、一鍵支持。">
<link rel="stylesheet" href="assets/style.css"></head><body>
{nav()}
<section class="hero"><div class="mosaic">{mosaic_html}</div><div class="wrap">
  <div class="eyebrow">Taiwan Sports Sponsorship</div>
  <h1>每一份支持，<br>都讓他們<em>更靠近夢想</em>。</h1>
  <p class="lead">從偏鄉國小的田徑隊到站上世界舞台的帕拉選手，這裡有 {len(records)} 個真實的故事。認識他們、理解他們需要什麼，然後成為他們路上的那股風。</p>
  <div class="cta"><a class="btn btn-accent" href="#browse">探索所有計畫</a><a class="btn btn-ghost" href="#featured">精選故事</a></div>
  <div class="stats"><div class="stat"><b class="num">{n_ath}</b><span>位運動員</span></div><div class="stat"><b class="num">{n_team}</b><span>支運動團隊</span></div><div class="stat"><b class="num">{len(sports)}</b><span>種運動項目</span></div><div class="stat"><b class="num">{n_remote}</b><span>個偏鄉計畫</span></div><div class="stat"><b class="num">{money(total_amount)}</b><span>總需求金額</span></div></div>
</div></section>

<section class="section" id="featured"><div class="wrap">
  <div class="section-head"><div><h2>精選故事</h2><p>有影片、有照片、有完整的成績與計畫——先從這三個開始認識。</p></div></div>
  <div class="featured">{feat_html}</div>
</div></section>

<section class="section" id="sports" style="padding-top:0"><div class="wrap">
  <div class="section-head"><div><h2>依運動種類探索</h2><p>點選項目，直接篩選下方清單。</p></div></div>
  <div class="chips"><button class="chip" data-sport="">全部<b>{len(records)}</b></button>{chips}</div>
</div></section>

<div class="filters" id="browse"><div class="wrap">
  <div class="seg"><button data-type="all" class="on">全部</button><button data-type="運動員">運動員</button><button data-type="運動團隊">運動團隊</button></div>
  <select id="sport"><option value="">所有運動種類</option>{sport_opts}</select>
  <select id="county"><option value="">所有縣市</option>{county_opts}</select>
  <label class="chk"><input type="checkbox" id="remote"> 只看偏鄉</label>
  <select id="sort"><option value="score">精選排序</option><option value="amount_desc">需求金額：高到低</option><option value="amount_asc">需求金額：低到高</option><option value="updated">最近更新</option><option value="name">名稱</option></select>
  <input id="q" type="search" placeholder="搜尋名字、學校、縣市、教練…">
  <span class="count" id="count"></span>
</div></div>
<section class="section" style="padding-top:34px"><div class="wrap"><div class="grid" id="grid"></div></div></section>
{footer()}
<script type="application/json" id="data">{data_json}</script>
<script src="assets/index.js"></script>
</body></html>"""

# ---------- detail ----------
MEDAL = [(r"金牌|第一名|第1名|冠軍|金", "g", "🥇"), (r"銀牌|第二名|第2名|亞軍", "s", "🥈"), (r"銅牌|第三名|第3名|季軍", "b", "🥉")]
def ach_li(text):
    yr = ""
    m = re.match(r"^[⟪《【\[]?\s*(\d{4})\s*年?\s*[⟫》】\]]?\s*(.*)$", text)
    if m and len(m.group(2)) > 2: yr, text = m.group(1), m.group(2)
    cls, icon = "", "•"
    for pat, c, ic in MEDAL:
        if re.search(pat, text): cls, icon = c, ic; break
    return f'<li><span class="medal {cls}">{icon}</span><div>{f"<span class=\"yr\">{yr}</span>" if yr else ""}{esc(text)}</div></li>'

def render_detail(r):
    rid = r["id"]; root = "../"
    nav_items = [("story", "我的故事"), ("results", "參賽成績"), ("profile", "基本資料"), ("plan", "關於計畫"), ("benefits", "預期效益"),
                 ("goals", "捐贈需求"), ("training", "我這樣訓練"), ("needs", "所以我需要"), ("contact", "聯絡人資訊")]
    if r["media"]: nav_items.append(("media", "媒體與社群"))
    subnav = "".join(f'<a href="#{k}">{v}</a>' for k, v in nav_items)
    cover = f' style="background-image:url(\'{root}{r["img"]["cover"]}\')"' if r["img"]["cover"] else ""
    pct = r.get("progress_pct", 0) or 0
    flags = " ".join(f'<span class="tag">{esc(f)}</span>' for f in r["flags"])
    where = f'<span>📍 {esc(r["region"] or "—")}</span>' + (f'<span>🏅 教練 {esc(r["coach"])}</span>' if r["coach"] else "") + (f'<span>🤝 推薦 {esc(info_get(r,"推薦者"))}</span>' if info_get(r, "推薦者") else "")
    sec_no = [0]
    def h2(title, sub=""):
        sec_no[0] += 1
        return f'<h2><span class="no">{sec_no[0]:02d}</span>{esc(title)}</h2>' + (f'<p class="sub">{esc(sub)}</p>' if sub else '<p class="sub"></p>')

    # 01 story
    story_pics = "".join(f'<img src="{root}{p}" alt="{esc(r["name"])} 故事圖片" loading="lazy">' for p in r["img"]["story"])
    quote = f'<div class="quote"><h4>推薦理由</h4>{paras(r["recommendation"])}</div>' if r.get("recommendation") else ""
    story_sec = f"""<section class="dsec" id="story"><div class="wrap">{h2("我的故事")}
      <div class="prose">{f'<div class="prose-title">{esc(r["story_title"])}</div>' if r.get("story_title") and r["story_title"]!=r["name"] else ""}{paras(r.get("story")) or ("" if story_pics else "<p>（官方頁面未填寫文字，請見下方圖片）</p>")}</div>
      {f'<div class="storypics">{story_pics}</div>' if story_pics else ""}{quote}</div></section>"""
    # 02 results
    ach = "".join(ach_li(a) for a in r["achievements"])
    upd = f"歷屆成績 · 更新於 {r['achievements_updated']}" if r.get("achievements_updated") else "歷屆成績"
    results_sec = f"""<section class="dsec" id="results"><div class="wrap">{h2("參賽成績", upd)}
      {f'<ul class="ach">{ach}</ul>' if ach else '<p class="note">官方頁面尚未填寫歷屆成績。</p>'}</div></section>"""
    # 03 profile
    kv = "".join(f'<div><small>{esc(k)}</small><b>{esc(v) or "—"}</b></div>' for k, v in r.get("info", []))
    gal = "".join(f'<a href="{root}{p}" data-full="{root}{p}" style="background-image:url(\'{root}{p}\')" aria-label="相關照片"></a>' for p in r["img"]["photos"])
    vids = "".join(f'<div class="video"><div class="fr"><iframe src="{esc(v["url"])}" loading="lazy" allowfullscreen title="{esc(v["title"] or "相關影片")}"></iframe></div>{f"<p>{esc(v[chr(116)+chr(105)+chr(116)+chr(108)+chr(101)])}</p>" if v.get("title") else ""}</div>' for v in r.get("videos", []))
    lnks = "".join(f'<a href="{esc(l["url"])}" target="_blank" rel="noopener">🔗 {esc(l["text"] or l["url"])}<small>{esc(l["url"])}</small></a>' for l in r.get("links", []) if l.get("url"))
    profile_sec = f"""<section class="dsec" id="profile"><div class="wrap">{h2("基本資料")}
      <div class="kv">{kv}</div>
      {f'<h3 class="sub-h">相關照片</h3><div class="gallery">{gal}</div>' if gal else ""}
      {f'<h3 class="sub-h">相關影片</h3><div class="videos">{vids}</div>' if vids else ""}
      {f'<h3 class="sub-h">相關連結</h3><div class="links">{lnks}</div>' if lnks else ""}
    </div></section>"""
    # 04 plan
    plan_pics = "".join(f'<img src="{root}{p}" alt="計畫圖片" loading="lazy">' for p in r["img"]["plan"])
    plan_sec = f"""<section class="dsec" id="plan"><div class="wrap">{h2("關於計畫", "訓練與參賽計畫")}
      <div class="prose">{f'<div class="prose-title">{esc(r["plan_title"])}</div>' if r.get("plan_title") and r["plan_title"]!=r["name"] else ""}{paras(r.get("plan")) or "<p>（尚未提供）</p>"}</div>
      {f'<div class="storypics">{plan_pics}</div>' if plan_pics else ""}</div></section>"""
    # 05 benefits
    benefits_sec = f"""<section class="dsec" id="benefits"><div class="wrap">{h2("預期效益")}<div class="prose">{paras(r.get("benefits")) or "<p>（尚未提供）</p>"}</div></div></section>"""
    # 06 goals
    goals = "".join(f'<li><span class="n">{i+1}</span><span>{esc(g)}</span></li>' for i, g in enumerate(r.get("goals", [])))
    goals_sec = f"""<section class="dsec" id="goals"><div class="wrap">{h2("捐贈需求", "我想達到…")}
      {f'<ul class="goals">{goals}</ul>' if goals else '<p class="note">（尚未提供）</p>'}</div></section>"""
    # 07 training
    periods = "".join(f'<div class="period"><h4><i></i>{esc(p["title"])}</h4><div class="t">{paras(p["body"])}</div></div>' for p in r.get("training_periods", []))
    methods = "".join(f'<div class="method"><h4>{esc(m["title"])}</h4><div class="t">{paras(m["body"])}</div></div>' for m in r.get("training_methods", []))
    training_sec = f"""<section class="dsec" id="training"><div class="wrap">{h2("我這樣訓練")}
      {f'<h3 class="sub-h" style="margin-top:0">訓練週期規劃</h3><div class="periods">{periods}</div>' if periods else ""}
      {f'<h3 class="sub-h">訓練方式</h3><div class="methods">{methods}</div>' if methods else ""}
      {"" if (periods or methods) else '<p class="note">（尚未提供）</p>'}</div></section>"""
    # 08 needs
    frows = "".join(f'<tr><td>{esc(n["item"])}</td><td>{esc(n["qty"].replace("$ ", "NT$ "))}</td></tr>' for n in r["fund_items"])
    if r["fund_items"]: frows += f'<tr class="total"><td>經費需求合計</td><td>{money(r["fund_total"])}</td></tr>'
    srows = "".join(f'<tr><td>{esc(n["item"])}</td><td>{esc(n["qty"])}</td></tr>' for n in r["supply_items"])
    needs_sec = f"""<section class="dsec" id="needs"><div class="wrap">{h2("所以我需要", "需求項目與數量（依官方頁面）")}
      <div class="needs">{f'<div class="needbox"><h4>經費需求</h4><table>{frows}</table></div>' if frows else ""}{f'<div class="needbox"><h4>物資需求</h4><table>{srows}</table></div>' if srows else ""}</div>
      {"" if (frows or srows) else '<p class="note">（尚未提供）</p>'}</div></section>"""
    # 09 contact
    ckv = "".join(f'<div><small>{esc(k)}</small><b>{esc(v) or "—"}</b></div>' for k, v in r.get("contact", []))
    contact_sec = f"""<section class="dsec" id="contact"><div class="wrap">{h2("聯絡人資訊")}<div class="contact">{ckv or '<p class="note">（尚未提供）</p>'}</div>
      <p class="note">標示「不公開」者為官方頁面未揭露之欄位。</p></div></section>"""
    # 10 media
    media_sec = ""
    if r["media"]:
        items = ""
        for l in r["media"]:
            src = esc(l.get("outlet") or l.get("source") or "")
            date = esc(l.get("date") or "")
            items += f'<a href="{esc(l["url"])}" target="_blank" rel="noopener"><div class="src"><i>{src}</i>{date}</div><b>{esc(l.get("title") or l["url"])}</b><p>{esc(l.get("summary") or "")}</p><span class="u">出處：{esc(l["url"])}</span></a>'
        media_sec = f"""<section class="dsec" id="media"><div class="wrap">{h2("媒體報導與社群", "網路公開搜尋結果，均附原始出處")}<div class="media">{items}</div></div></section>"""
    # related
    same = [x for x in records if x["id"] != rid and x["sport"] == r["sport"]]
    others = [x for x in records if x["id"] != rid and x["sport"] != r["sport"]]
    random.seed(rid); rel = (same[:4] + random.sample(others, min(4, len(others))))[:4]
    related = "".join(card_html(x, root) for x in rel)

    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(r['name'])}｜{esc(r['sport'])}{esc(r['type'])}｜為台灣運動員而跑</title>
<meta name="description" content="{esc(r['excerpt'])}">
<meta property="og:title" content="{esc(r['name'])}｜{esc(r['tagline'])}"><meta property="og:description" content="{esc(r['excerpt'])}">{f'<meta property="og:image" content="{root}{r["img"]["cover"]}">' if r["img"]["cover"] else ""}
<link rel="stylesheet" href="../assets/style.css"></head><body>
{nav(root)}
<section class="dhero"><div class="wrap">
  <div class="pic"{cover}></div>
  <div>
    <div class="crumb"><a href="{root}index.html">所有計畫</a> / {esc(r['sport'])} / {esc(r['type'])}</div>
    {type_tag(r)}
    <h1>{esc(r['name'])}</h1>
    <p class="tagline">{esc(r['tagline']) if r['tagline']!=r['name'] else esc(r['excerpt'])}</p>
    <div class="where">{where}</div>
    <div class="need"><div class="row"><div><span>需求金額</span><br><b class="num">{money(r.get('amount'))}</b></div><div class="tags">{flags}</div></div>
      <div class="bar"><i style="width:{min(100,pct)}%"></i></div><div class="pct"><span>目前達成 {pct:g}%</span><span>資料時間 {SCRAPE_DATE}</span></div></div>
    <div class="cta"><a class="btn btn-accent" href="{esc(r['source_url'])}" target="_blank" rel="noopener">前往官方平臺捐贈 ↗</a><button class="btn btn-ghost" id="share">分享此頁</button></div>
  </div>
</div></section>
<div class="subnav"><div class="wrap">{subnav}</div></div>
{story_sec}{results_sec}{profile_sec}{plan_sec}{benefits_sec}{goals_sec}{training_sec}{needs_sec}{contact_sec}{media_sec}
<section class="section related"><div class="wrap"><div class="section-head"><div><h2>你可能也想認識</h2><p>同項目與其他運動的計畫</p></div><a class="btn btn-line btn-sm" href="{root}index.html#browse">查看全部 {len(records)} 個計畫</a></div><div class="grid">{related}</div></div></section>
{footer()}
<div class="lb" id="lb"><img alt=""></div>
<a class="btn btn-line btn-sm back-top" href="#top">↑ 回頂端</a>
<script src="../assets/detail.js"></script>
</body></html>"""

# ---------- write ----------
with open(os.path.join(OUT, "assets", "style.css"), "w", encoding="utf-8") as f: f.write(CSS)
with open(os.path.join(OUT, "assets", "index.js"), "w", encoding="utf-8") as f: f.write(JS_INDEX)
with open(os.path.join(OUT, "assets", "detail.js"), "w", encoding="utf-8") as f: f.write(JS_DETAIL)
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f: f.write(render_index())
for r in records:
    with open(os.path.join(OUT, "p", f"{r['id']}.html"), "w", encoding="utf-8") as f: f.write(render_detail(r))
# site data export (clean, without raw tokens)
export = []
for r in records:
    e = {k: v for k, v in r.items() if k not in ("token", "cover_list", "need_flags_list", "order", "images", "score")}
    export.append(e)
with open(os.path.join(OUT, "data", "athletes.json") if os.path.isdir(os.path.join(OUT, "data")) else os.path.join(OUT, "athletes.json"), "w", encoding="utf-8") as f:
    json.dump(export, f, ensure_ascii=False, indent=1)
print("built", len(records), "pages ->", OUT)
