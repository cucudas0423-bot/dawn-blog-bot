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

    # 검증 게이트: 운영자 매매 노출·AI 말투·기준일
    LEAK = [r"제 계좌", r"제가 실제로 (산|샀|매수|매도|팔)", r"(내|제) 매매 ?규칙", r"(내|제) 수익률",
            r"SOXL[^.。]{0,30}(매수|매도) ?기준", r"\d+ ?분할 ?매수"]
    for pat in LEAK:
        m = re.search(pat, text)
        if m:
            warns.append(f"운영자 매매 노출 의심 표현: '{text[max(0, m.start()-15):m.end()+15]}'")
    AI = ["매우 중요한", "혁신적인", "획기적인", "다양한 방법", "효과적인 전략", "결론적으로", "요약하자면",
          "살펴보겠습니다", "알아보겠습니다", "무엇보다 중요한", "한층 더"]
    hits = [w for w in AI if w in text]
    if len(hits) >= 3:
        warns.append("AI 말투 후보가 많아요: " + ", ".join(hits))
    if not re.search(r"20\d\d[.\-년] ?\d{1,2}[.\-월]? ?(\d{1,2}일?)?\s*(기준|확인)", text):
        warns.append("숫자 확인 기준일(예: 2026.11.4 기준)이 본문에 안 보여요")

srcs = meta.get("sources") or []
bad = [s for s in srcs if not str(s.get("url", "")).startswith("http")]
if len(srcs) < 2:
    errs.append(f"출처가 {len(srcs)}개예요(최소 2개)")
if bad:
    errs.append(f"주소가 없는 출처가 {len(bad)}개 있어요")

try:
    olds = json.load(open(os.path.join(W, "existing_posts.json"), encoding="utf-8"))
    if any((o.get("title") or "").strip() == (meta.get("title") or "").strip() for o in olds):
        errs.append("같은 제목의 글이 이미 있어요(중복 저장 방지)")
except (OSError, ValueError):
    pass

json.dump({"errors": errs, "warnings": warns}, open(os.path.join(W, "check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for w in warns:
    print("주의:", w)
if errs:
    print("\n".join("오류: " + e for e in errs))
    sys.exit(1)
print("검사 통과:", meta.get("title"))
