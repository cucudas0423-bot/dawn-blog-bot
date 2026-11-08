"""연재 7·10·11·12·13편에 '실제로 Claude에게 이렇게 시켰어요' 코너를 넣어요 (마무리 소제목 바로 앞).

사용: python scripts/add_captures.py           # 넣을 곳만 보여줌(dry-run)
      python scripts/add_captures.py --apply   # 실제로 수정
"""
import html as H
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402
from restyle_posts import all_posts  # noqa: E402

RAW = "https://raw.githubusercontent.com/cucudas0423-bot/dawn-blog-bot/main/images/capture/"
MARK = "실제로 Claude에게 이렇게 시켰어요"

C = {
    5: {
        "intro": "API 신청하면서 헷갈린 건 그냥 물어봤어요. 모의투자는 키 없이 되는 줄 알았는데, 한 줄 물어보니 바로 정리해 줬어요.",
        "imgs": [("c5_key.png", "모의투자 키를 물어본 실제 대화예요.")],
        "say": ["모의투자에서도 App Key가 필요해? 받는 순서를 알려줘",
                "실전투자 키와 모의투자 키는 뭐가 달라?"],
    },
    6: {
        "intro": "키를 코드에 직접 넣는 게 불안해서, 입력 창을 만들어 달라고 했어요. 영어로 대충 써도 알아들어요.",
        "imgs": [("c6_popup.png", "키 입력 창을 시킨 실제 대화예요.")],
        "say": ["앱 키와 시크릿을 입력하는 창을 띄워줘",
                "키가 연결됐는지 화면에서 바로 보이게 해줘"],
    },
    7: {
        "intro": "처음에는 거창한 설계서 없이 시작했어요. 키움 공식 깃허브 주소 하나 붙이고 <b>무엇을 할 수 있어야 하는지</b>만 줄줄이 적었어요.",
        "imgs": [("c7_start.png", "자동매매를 처음 시킨 날의 실제 대화예요.")],
        "say": ["[키움 REST API 깃허브 주소] 주소의 샘플코드를 참고해서 미국주식 현재가를 보고 LOC로 매수·매도할 수 있는 웹사이트를 만들어줘. python fastapi로 만들어줘."],
    },
    10: {
        "intro": "카카오톡 알림은 <b>몇 시에, 무엇을</b> 받고 싶은지만 말했어요. 그리고 바로 \"하나 보내줘봐\"로 시험했어요.",
        "imgs": [("c10_kakao.png", "카카오톡 알림을 시킨 실제 대화예요.")],
        "say": ["체결 결과를 아침 7시에 카카오톡 나에게 보내기로 보내줘",
                "카카오톡으로 테스트 메시지 하나 보내줘봐"],
    },
    11: {
        "intro": "막혔을 때도 말로 풀었어요. 모의투자에서 LOC가 안 될 때는 방향만 정해 줬고, AI가 짐작으로 짠 것 같을 때는 짐작한 걸 다 꺼내 보라고 했어요.",
        "imgs": [("c11_sim.png", "모의투자 LOC 문제를 해결한 실제 대화예요."),
                 ("c11_noguess.png", "AI에게 짐작한 부분을 밝히라고 한 실제 대화예요.")],
        "after": "두 번째 말이 제일 효과가 컸어요. AI는 모르는 부분을 그럴듯하게 채우는 버릇이 있어서, 주문 코드에서는 <b>\"매뉴얼대로 확인해\"</b>를 꼭 붙이는 게 좋아요.",
        "say": ["모의투자에서 LOC가 안 되면, 실제 종가로 계산만 하는 가상 체결 모드로 돌려줘",
                "지금 코드에서 매뉴얼로 확인하지 않고 짐작한 부분이 있으면 전부 알려줘"],
    },
    12: {
        "intro": "서버로 옮긴 것도 질문 하나에서 시작했어요. \"PC 꺼도 돌아가?\" 하고 물었고, 안 된다길래 \"무료 서버로 일단 쓰자\"고 했어요.",
        "imgs": [("c12_server.png", "무료 서버로 옮길 때의 실제 대화예요.")],
        "say": ["자동매매는 컴퓨터를 꺼도 돌아가?",
                "무료 서버로 옮겨줘. 내가 직접 해야 하는 건 순서대로 알려줘"],
    },
    13: {
        "intro": "운영도 한 줄로 시켰어요. 서버가 걱정되면 감시를 만들자고 하면 돼요.",
        "imgs": [("c13_watch.png", "서버 감시를 시킨 실제 대화예요.")],
        "say": ["서버가 멈추면 알림이 오게 서버다운 감시를 따로 만들자",
                "서버 데이터를 PC로 백업하는 명령어 알려줘"],
    },
}

P = "margin:0 0 20px;"
H2 = "color:#1d2026;font-size:22px;font-weight:700;line-height:1.5;margin:60px 0 22px;"
BOX = "background:#f7f5f1;border-left:3px solid #c98a3c;margin:28px 0;padding:16px 20px;"


def block(c):
    out = [f'<h2 style="{H2}">{MARK}</h2>', f'<p style="{P}">{c["intro"]}</p>']
    for f, cap in c["imgs"]:
        out.append(f'<div style="margin:28px 0 12px;text-align:center;"><img alt="{H.escape(cap)}" src="{RAW}{f}" '
                   f'style="border-radius:4px;height:auto;max-width:100%;" width="1080"/>'
                   f'<div style="color:#8a8f98;font-size:14px;margin-top:8px;">{H.escape(cap)}</div></div>')
    if c.get("after"):
        out.append(f'<p style="{P}">{c["after"]}</p>')
    lis = "".join(f'<li style="margin-bottom:10px;">"{H.escape(s)}"</li>' for s in c["say"])
    out.append(f'<div style="{BOX}"><p style="{P}"><b>이 말 그대로 따라 써 보세요</b></p>'
               f'<ul style="margin:0;padding-left:22px;">{lis}</ul></div>')
    return BeautifulSoup("".join(out), "html.parser")


def main():
    apply = "--apply" in sys.argv
    tok = blogger.access_token()
    posts = all_posts(tok)
    os.makedirs("backup", exist_ok=True)
    json.dump([{"id": p["id"], "title": p["title"], "content": p.get("content", "")} for p in posts],
              open("backup/posts_before_captures.json", "w", encoding="utf-8"), ensure_ascii=False)
    for n, c in C.items():
        hits = [p for p in posts if f"자동매매 {n}편)" in p["title"]]
        if not hits:
            print(f"[{n}편] 글을 못 찾음")
            continue
        p = hits[0]
        html = p.get("content", "")
        soup = BeautifulSoup(html, "html.parser")
        old = next((h for h in soup.find_all("h2") if MARK in h.get_text()), None)
        if old is not None:
            # 예전 코너(소제목 ~ '따라 써 보세요' 박스)를 지우고 새로 넣어요
            node = old
            while node is not None:
                nxt = node.find_next_sibling()
                done = "따라 써 보세요" in node.get_text()
                node.decompose()
                if done:
                    break
                node = nxt
            print(f"[{n}편] 예전 코너 지움")
        anchor = next((h for h in soup.find_all("h2") if "마무리" in h.get_text()), None)
        if anchor is None:
            anchor = next((x for x in reversed(soup.find_all("p")) if re.search(r"투자 판단|책임", x.get_text())), None)
        if anchor is None:
            print(f"[{n}편] 넣을 위치를 못 찾음: {p['title'][:40]}")
            continue
        anchor.insert_before(block(c))
        print(f"[{n}편] {p['title'][:44]} → '{anchor.get_text()[:20]}' 앞에 추가")
        if apply:
            r = requests.patch(f"{blogger.API}/blogs/{blogger.blog_id()}/posts/{p['id']}", headers=blogger._h(tok),
                               json={"content": str(soup)}, timeout=60)
            print("   ", "완료" if r.status_code == 200 else f"실패 {r.status_code} {r.text[:150]}")


if __name__ == "__main__":
    main()
