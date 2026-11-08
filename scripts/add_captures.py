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
    7: {
        "intro": "저도 처음엔 거창한 설계서 없이 시작했어요. 키움 공식 깃허브 주소 하나 붙이고 \"만들어줘\"라고 했어요. 문장이 매끄럽지 않아도 되고, 영어와 한글이 섞여도 AI는 알아들어요. 중요한 건 <b>무엇을 할 수 있어야 하는지</b>를 줄줄이 적어주는 거예요.",
        "imgs": [("p1_start.png", "자동매매를 처음 시킨 날의 실제 대화예요. 종목명은 가렸어요.")],
        "say": ["[키움 REST API 깃허브 주소] 주소의 샘플코드를 참고해서 미국주식 현재가를 보고 LOC로 매수·매도할 수 있는 웹사이트를 만들어줘. python fastapi로 만들어줘.",
                "앱 키와 시크릿을 입력하는 창을 띄워줘",
                "모의투자와 실전투자는 키가 따로야? 어디서 바꾸는지 화면에 잘 보이게 해줘"],
    },
    10: {
        "intro": "카카오톡 알림도 코드를 직접 짜지 않았어요. <b>몇 시에, 무엇을</b> 받고 싶은지만 말했어요. 그리고 꼭 \"지금 하나 보내줘봐\"로 바로 시험해 봤어요.",
        "imgs": [("p2_kakao.png", "카카오톡 알림을 시킨 실제 대화예요.")],
        "say": ["체결 결과를 아침 7시에 카카오톡 나에게 보내기로 보내줘",
                "서버 다시 시작하고, 카카오톡으로 테스트 메시지 하나 보내줘봐",
                "주문이 나가면 나간 결과를 카카오톡으로 바로 알려줘"],
    },
    11: {
        "intro": "막혔을 때도 말로 풀었어요. 모의투자에서 LOC가 안 된다는 걸 알았을 때는 방향만 정해줬고, AI가 제 말을 반만 들었을 때는 그냥 짜증 섞인 말투 그대로 다시 시켰어요.",
        "imgs": [("p4_trial.png", "모의투자 LOC 문제와 화면 정리를 시킨 실제 대화예요."),
                 ("p5_noguess.png", "주문이 사라진 날의 실제 대화예요. 이 뒤로 AI가 확인한 것과 짐작한 것을 나눠서 말해줬어요.")],
        "after": "제일 크게 배운 건 두 번째 캡쳐예요. AI는 모르는 부분을 그럴듯하게 짐작해서 채우는 버릇이 있어요. 돈이 오가는 주문 코드에서는 이게 위험해요. <b>\"추측하지 말고 매뉴얼대로 확인해\"</b>라고 말하고, 짐작한 부분을 목록으로 달라고 하니 훨씬 정확해졌어요.",
        "say": ["모의투자에서 LOC가 안 되면, 실제 종가로 계산만 하는 가상 체결 모드로 돌려줘",
                "추측하지 말고 공식 매뉴얼대로 확인해서 다시 고쳐",
                "지금 코드에서 매뉴얼로 확인하지 않고 짐작한 부분이 있으면 전부 알려줘"],
    },
    12: {
        "intro": "서버로 옮긴 것도 질문 하나에서 시작했어요. \"PC 꺼도 돌아가?\"라고 물었고, 안 된다길래 \"무료 서버로 일단 쓰자\"고 했어요. 가입이나 카드 인증처럼 AI가 대신 못 하는 일은 AI가 순서대로 알려주고, 저는 화면에서 막히는 것만 물어봤어요.",
        "imgs": [("p3_server.png", "무료 서버로 옮길 때의 실제 대화예요.")],
        "say": ["자동매매는 컴퓨터를 꺼도 돌아가?",
                "무료 서버로 옮겨줘. 내가 직접 해야 하는 건 순서대로 알려줘",
                "홈 리전에 한국이 없는데 일본으로 해도 돼?"],
    },
    13: {
        "intro": "운영도 대부분 한 줄로 시켰어요. 백업 명령어가 필요하면 \"백업명령해줘\", 서버가 걱정되면 \"감시를 따로 만들자\"였어요. 명령어를 외울 필요가 없어요.",
        "imgs": [("p6_ops.png", "운영 점검을 시킨 실제 대화예요. 서버 주소와 키 파일 경로는 가렸어요.")],
        "say": ["서버 데이터를 PC로 백업하는 명령어 알려줘",
                "서버가 멈추면 알림이 오게 서버다운 감시를 따로 만들자",
                "이상이 있으면 카카오톡으로 알려줘"],
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
        if MARK in html:
            print(f"[{n}편] 이미 있음")
            continue
        soup = BeautifulSoup(html, "html.parser")
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
