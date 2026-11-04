"""이미 올린 글(발행·예약·임시저장)의 면책 문구 끝에 AI 활용 안내 한 줄을 붙여요.

사용: python scripts/add_ai_notice.py           # 붙일 곳만 보여줌(dry-run)
      python scripts/add_ai_notice.py --apply   # 실제로 수정
"""
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402
from restyle_posts import all_posts  # noqa: E402

LINE = "이 글은 AI의 도움을 받아 자료를 정리하고, 운영자가 확인해 올립니다."
KEY = re.compile(r"투자 ?(권유|판단|결정)|책임|참고용|정보 제공")


def find_disc(soup):
    ps = [p for p in soup.find_all(["p", "div"]) if KEY.search(p.get_text()) and not p.find(["p", "div"])]
    small = [p for p in ps if "13px" in (p.get("style") or "") or "border-top" in (p.get("style") or "")]
    return (small or ps or [None])[-1]


def main():
    apply = "--apply" in sys.argv
    tok = blogger.access_token()
    posts = all_posts(tok)
    os.makedirs("backup", exist_ok=True)
    json.dump([{"id": p["id"], "status": p["_status"], "title": p["title"], "content": p.get("content", "")} for p in posts],
              open("backup/posts_before_ai_notice.json", "w", encoding="utf-8"), ensure_ascii=False)
    done = skip = miss = 0
    for p in posts:
        html = p.get("content", "")
        if "AI의 도움" in html:
            skip += 1
            continue
        soup = BeautifulSoup(html, "html.parser")
        d = find_disc(soup)
        if d is None:
            miss += 1
            print(f"[못 찾음] [{p['_status']}] {p['title'][:50]}")
            continue
        print(f"[{p['_status']}] {p['title'][:46]}  ←  …{d.get_text(' ', strip=True)[-50:]}")
        d.append(" " + LINE)
        if apply:
            r = requests.patch(f"{blogger.API}/blogs/{blogger.blog_id()}/posts/{p['id']}", headers=blogger._h(tok),
                               json={"content": str(soup)}, timeout=60)
            if r.status_code != 200:
                print("   수정 실패:", r.status_code, r.text[:150])
                continue
        done += 1
    print(f"\n{'붙인' if apply else '붙일'} 글: {done}개 · 이미 있음: {skip}개 · 면책 문구 못 찾음: {miss}개")


if __name__ == "__main__":
    main()
