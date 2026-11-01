"""임시저장된 글을 발행(또는 예약 발행)해요.

영문 제목으로 바꿔 발행해서 깔끔한 주소(slug)를 만들고, 곧바로 한글 제목으로 되돌려요.
  python scripts/publish_draft.py <글ID> [now | "YYYY-MM-DD HH:MM"]
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = dt.timezone(dt.timedelta(hours=9))

pid = sys.argv[1].strip()
when = (sys.argv[2] if len(sys.argv) > 2 else "now").strip() or "now"
rec_path = os.path.join(ROOT, "drafts", f"{pid}.json")
if not os.path.exists(rec_path):
    sys.exit(f"drafts/{pid}.json 기록이 없어요. 글 ID를 확인해 주세요.")
rec = json.load(open(rec_path, encoding="utf-8"))

tok = blogger.access_token()
blogger.update_title(tok, pid, rec["title_en"])
if when == "now":
    t = dt.datetime.now(KST) + dt.timedelta(minutes=1)
else:
    t = dt.datetime.strptime(when, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
p = blogger.schedule_post(tok, pid, t.isoformat())
p = blogger.update_title(tok, pid, rec["title"])
print("발행 완료:" if when == "now" else f"{t:%m월 %d일 %H:%M} 예약 완료:", p.get("url"))
os.remove(rec_path)
