"""이미 올린 글(발행·예약·임시저장)의 'AI 티' 나는 꾸밈을 차분한 스타일로 바꿔요.

- 파란 밑줄·초록 굵은 강조 → 평범한 굵게
- 주황 요약 박스 → 옅은 바탕 + 왼쪽 선
- 큰따옴표 장식 인용구 → 왼쪽 선 인용
- 남색 소제목·회색 표 머리 → 차분한 색

사용: python scripts/restyle_posts.py            # 바꿀 곳만 보여줌(dry-run)
      python scripts/restyle_posts.py --apply    # 실제로 수정
"""
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402

API = blogger.API


def hexify(v: str) -> str:
    v = v.strip().lower().replace(" ", "")
    m = re.fullmatch(r"rgba?\((\d+),(\d+),(\d+)(?:,[\d.]+)?\)", v)
    if m:
        return "#%02x%02x%02x" % tuple(int(x) for x in m.groups())
    return v


def parse(style: str) -> dict:
    d = {}
    for part in (style or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            d[k.strip().lower()] = v.strip()
    return d


def dump(d: dict) -> str:
    return "".join(f"{k}:{v};" for k, v in d.items())


BLUE = {"#1a56db"}
GREEN = {"#188038"}
BOX = "background:#f7f5f1;border-left:3px solid #c98a3c;margin:28px 0;padding:16px 20px;"
FAQ = "border-bottom:1px solid #ebe7df;margin:0 0 8px;padding:14px 0;"
QUOTE = ("border-left:3px solid #c98a3c;color:#3a3d44;font-size:17px;line-height:1.8;"
         "margin:36px 0;padding:4px 0 4px 18px;")


def restyle(html: str):
    soup = BeautifulSoup(html, "html.parser")
    n = {"강조": 0, "박스": 0, "FAQ": 0, "인용": 0, "소제목": 0, "표": 0}

    for e in soup.find_all(style=True):
        st = parse(e["style"])
        col = hexify(st.get("color", ""))
        bg = hexify(st.get("background", st.get("background-color", "")))

        if e.name in ("b", "strong", "span") and (col in BLUE or col in GREEN):
            for k in ("color", "text-decoration", "text-decoration-line", "text-underline-offset"):
                st.pop(k, None)
            if st:
                e["style"] = dump(st)
            else:
                del e["style"]
            n["강조"] += 1
        elif e.name == "div" and bg == "#fff7ef":
            e["style"] = BOX
            n["박스"] += 1
        elif e.name == "div" and bg == "#f5f7fb" and "border-radius" in st:
            e["style"] = FAQ
            n["FAQ"] += 1
        elif e.name == "h2" and col == "#1f3a68":
            st["color"] = "#1d2026"
            e["style"] = dump(st)
            n["소제목"] += 1
        elif e.name == "th" and bg == "#c4c7cc":
            st.pop("background-color", None)
            st["background"] = "#f1eee8"
            if "border" in st:
                st["border"] = "1px solid #e2ddd3"
            e["style"] = dump(st)
            n["표"] += 1
        elif e.name == "td" and "#dcdfe4" in st.get("border", ""):
            st["border"] = "1px solid #e2ddd3"
            e["style"] = dump(st)

    # 큰따옴표 장식 인용구
    for bq in soup.find_all("blockquote"):
        marks = [d for d in bq.find_all("div") if hexify(parse(d.get("style")).get("color", "")) == "#c9ced8"]
        if not marks:
            continue
        for d in marks:
            d.decompose()
        p = bq.find("p")
        new = soup.new_tag("p", style=QUOTE)
        if p:
            new.append(BeautifulSoup(p.decode_contents(), "html.parser"))
        bq.replace_with(new)
        n["인용"] += 1

    return str(soup), n


def all_posts(tok):
    out = []
    for status in ("live", "scheduled", "draft"):
        page = None
        while True:
            params = {"status": status, "view": "ADMIN", "fetchBodies": "true", "maxResults": 50}
            if page:
                params["pageToken"] = page
            r = requests.get(f"{API}/blogs/{blogger.blog_id()}/posts", headers=blogger._h(tok), params=params, timeout=60)
            r.raise_for_status()
            j = r.json()
            for p in j.get("items", []):
                p["_status"] = status
                out.append(p)
            page = j.get("nextPageToken")
            if not page:
                break
    return out


def main():
    apply = "--apply" in sys.argv
    tok = blogger.access_token()
    total = 0
    for p in all_posts(tok):
        new, n = restyle(p.get("content", ""))
        changed = sum(n.values())
        if not changed:
            continue
        total += 1
        detail = ", ".join(f"{k} {v}" for k, v in n.items() if v)
        print(f"[{p['_status']}] {p['title'][:50]} → {detail}")
        if apply:
            r = requests.patch(f"{API}/blogs/{blogger.blog_id()}/posts/{p['id']}",
                               headers=blogger._h(tok), json={"content": new}, timeout=60)
            if r.status_code != 200:
                print("   수정 실패:", r.status_code, r.text[:200])
            else:
                print("   수정 완료")
    print(f"\n{'수정한' if apply else '바꿀'} 글: {total}개" + ("" if apply else "  (dry-run, 실제 수정은 --apply)"))


if __name__ == "__main__":
    main()
