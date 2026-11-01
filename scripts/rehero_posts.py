"""이미 올린 글의 대표 이미지(본문 첫 번째 이미지)를 새 사진 배경 디자인으로 바꿔요.

Claude 없이 글 제목·라벨·날짜만으로 만들어요.
사용: python scripts/rehero_posts.py           # 이미지만 만들어 work/rehero/ 에 저장(dry-run)
      python scripts/rehero_posts.py --apply   # 이미지를 저장소에 올리고 글의 첫 이미지를 교체
"""
import datetime as dt
import glob
import hashlib
import html as H
import json
import os
import re
import subprocess
import sys

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402
from restyle_posts import all_posts  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "work", "rehero")
HEROES = sorted(glob.glob(os.path.join(ROOT, "templates", "heroes", "*.jpg")))
API = blogger.API


def split_title(title: str):
    """제목을 (작은 머리말, 큰 제목, 부제)로 나눠요."""
    kicker = ""
    m = re.search(r"\((미국 ETF LOC 자동매매 \d+편)\)\s*$", title)
    if m:
        kicker = m.group(1)
        title = title[: m.start()].strip()
    year = ""
    m = re.search(r"\s*(\([^()]*20\d\d[^()]*\))\s*$", title)
    if m:
        year = m.group(1)
        title = title[: m.start()].strip()
    cands = []
    for sep in (", ", "? ", "… ", ": "):
        i = title.find(sep)
        while i != -1:
            if i >= 8:
                cands.append((i, sep))
                break
            i = title.find(sep, i + 1)
    if cands:
        i, sep = min(cands)
        head = title[:i] + (sep.strip() if sep.strip() in "?…" else "")
        rest = title[i + len(sep):]
        return kicker, head.strip(), (rest + (" " + year if year else "")).strip()
    return kicker, title, year


def hero_html(kicker, head, lead, date_str, photo):
    size = 34 if len(head) <= 22 else 30 if len(head) <= 30 else 27
    width = 440 if len(head) <= 26 else 540
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{ROOT}/templates/card.css"></head><body>
<div id="card" class="hero" style='--hero:url("file://{photo}")'>
  <div class="in" style="width:{width}px">
    {f'<div class="kicker">{H.escape(kicker)}</div>' if kicker else ''}
    <h1 style="font-size:{size}px">{H.escape(head)}</h1>
    {f'<p class="lead">{H.escape(lead)}</p>' if lead else ''}
  </div>
  <div class="foot"><span>{date_str}</span><span>새벽 4시의 자동매매</span></div>
</div></body></html>"""


def sh(*a, check=True):
    return subprocess.run(a, cwd=ROOT, check=check, text=True, capture_output=True)


def main():
    apply = "--apply" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    tok = blogger.access_token()
    posts = all_posts(tok)
    json.dump([{"id": p["id"], "status": p["_status"], "title": p["title"], "content": p.get("content", "")} for p in posts],
              open(os.path.join(OUT, "posts_before_rehero.json"), "w", encoding="utf-8"), ensure_ascii=False)

    jobs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 760, "height": 600}, device_scale_factor=2)
        for p in posts:
            soup = BeautifulSoup(p.get("content", ""), "html.parser")
            first = soup.find("img")
            if not first:
                print(f"[건너뜀] 이미지 없음: {p['title'][:40]}")
                continue
            labels = p.get("labels", [])
            kicker, head, lead = split_title(p["title"])
            if not kicker:
                cat = soup.find(string=re.compile(r"새벽 4시의 자동매매\s*·"))
                kicker = cat.split("·", 1)[1].strip() if cat else (labels[0] if labels else "")
            when = p.get("published") or p.get("updated") or ""
            try:
                d = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
                date_str = f"{d.year}.{d.month}.{d.day}"
            except ValueError:
                date_str = ""
            photo = HEROES[int(hashlib.md5(p["id"].encode()).hexdigest(), 16) % len(HEROES)]
            hp = os.path.join(OUT, f"{p['id']}.html")
            open(hp, "w", encoding="utf-8").write(hero_html(kicker, head, lead, date_str, photo))
            pg.goto("file://" + hp)
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            path = os.path.join(OUT, f"{p['id']}.png")
            pg.query_selector("#card").screenshot(path=path)
            print(f"[{p['_status']}] {p['title'][:46]}  →  {kicker} / {head} / {lead}")
            jobs.append((p, path))
        b.close()

    # 한눈에 보기용 모음 이미지
    try:
        from PIL import Image
        ims = [Image.open(j[1]).convert("RGB").resize((380, 214)) for j in jobs]
        cols = 3
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 386, rows * 220), "white")
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 386, (i // cols) * 220))
        sheet.save(os.path.join(OUT, "_sheet.jpg"), quality=80)
    except Exception as e:  # noqa: BLE001
        print("모음 이미지 실패:", e)

    if not apply:
        print(f"\n만든 대표 이미지: {len(jobs)}개 (dry-run, 교체는 --apply)")
        return

    # 1) 저장소에 올리기
    repo = os.environ["GITHUB_REPOSITORY"]
    dest = os.path.join(ROOT, "images", "hero")
    os.makedirs(dest, exist_ok=True)
    urls = {}
    for p, path in jobs:
        name = f"{p['id']}.png"
        os.replace(path, os.path.join(dest, name))
        urls[p["id"]] = f"https://raw.githubusercontent.com/{repo}/main/images/hero/{name}"
    sh("git", "add", "images/hero")
    sh("git", "commit", "-m", f"hero images for {len(urls)} posts")
    for _ in range(3):
        if sh("git", "push", check=False).returncode == 0:
            break
        sh("git", "pull", "--rebase", check=False)

    # 2) 글의 첫 이미지 교체
    ok = 0
    for p, _ in jobs:
        soup = BeautifulSoup(p.get("content", ""), "html.parser")
        img = soup.find("img")
        old = img.get("src", "")
        img["src"] = urls[p["id"]]
        for a in ("srcset", "data-original-height", "data-original-width", "height"):
            if img.has_attr(a):
                del img[a]
        img["width"] = "1080"
        st = img.get("style", "")
        if "height:auto" not in st.replace(" ", ""):
            img["style"] = (st.rstrip(";") + ";height:auto;max-width:100%;").lstrip(";")
        par = img.find_parent("a")
        if par and par.get("href") == old:
            par["href"] = urls[p["id"]]
        r = requests.patch(f"{API}/blogs/{blogger.blog_id()}/posts/{p['id']}", headers=blogger._h(tok),
                           json={"content": str(soup)}, timeout=60)
        if r.status_code == 200:
            ok += 1
        else:
            print("교체 실패:", p["title"][:40], r.status_code, r.text[:150])
    print(f"\n대표 이미지 교체: {ok}/{len(jobs)}개")


if __name__ == "__main__":
    main()
