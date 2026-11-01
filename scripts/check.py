"""Claude가 만든 결과물(work/)이 업로드 가능한 상태인지 검사해요."""
import json
import os
import re
import sys

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "work")
errs, warns = [], []

try:
    meta = json.load(open(os.path.join(W, "post.json"), encoding="utf-8"))
except Exception as e:  # noqa: BLE001
    sys.exit(f"work/post.json 을 읽을 수 없어요: {e}")

for k in ("title", "title_en", "labels", "description", "topic_reason", "sources"):
    if not meta.get(k):
        errs.append(f"post.json 에 '{k}' 가 없어요")
if meta.get("title") and len(meta["title"]) > 70:
    warns.append(f"제목이 길어요({len(meta['title'])}자)")
if meta.get("title_en") and not re.fullmatch(r"[A-Za-z0-9 \-]+", meta["title_en"]):
    errs.append("title_en 은 영문/숫자/공백/하이픈만 써야 해요")

p = os.path.join(W, "body.html")
if not os.path.exists(p):
    errs.append("work/body.html 이 없어요")
else:
    soup = BeautifulSoup(open(p, encoding="utf-8").read(), "html.parser")
    text = soup.get_text(" ", strip=True)
    if len(text) < 2500:
        errs.append(f"본문이 너무 짧아요({len(text)}자, 최소 2500자)")
    h2 = soup.find_all("h2")
    if len(h2) < 4:
        errs.append(f"h2 소제목이 {len(h2)}개예요(최소 4개)")
    imgs = soup.find_all("img", attrs={"data-g": True})
    if not 3 <= len(imgs) <= 7:
        errs.append(f"그래픽이 {len(imgs)}개예요(3~7개)")
    for im in imgs:
        g = im["data-g"]
        if not os.path.exists(os.path.join(W, "graphics", f"g{g}.png")):
            errs.append(f"g{g}.png 가 렌더링되지 않았어요")
        if not im.get("alt"):
            errs.append(f"g{g} 이미지에 alt 가 없어요")
    if not soup.find("p", class_="disc"):
        errs.append("면책 문구(<p class=\"disc\">)가 없어요")

for w in warns:
    print("주의:", w)
if errs:
    print("\n".join("오류: " + e for e in errs))
    sys.exit(1)
print("검사 통과:", meta.get("title"))
