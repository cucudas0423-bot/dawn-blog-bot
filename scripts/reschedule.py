"""예약·임시저장 글의 발행 시각을 바꾸거나 바로 발행해요.

사용: python scripts/reschedule.py "글ID=now;글ID=2026-11-05 07:00;..."   (서울 시간)
"""
import datetime as dt
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402

KST = dt.timezone(dt.timedelta(hours=9))
API = blogger.API


def main():
    plan = [x.split("=", 1) for x in sys.argv[1].split(";") if "=" in x]
    tok = blogger.access_token()
    for pid, when in plan:
        pid, when = pid.strip(), when.strip()
        base = f"{API}/blogs/{blogger.blog_id()}/posts/{pid}"
        cur = requests.get(base, headers=blogger._h(tok), params={"view": "ADMIN"}, timeout=60).json()
        title, status = cur.get("title", "?"), cur.get("status", "?")
        if status == "LIVE":
            print(f"[건너뜀] 이미 발행된 글: {title}")
            continue
        if status == "SCHEDULED":
            r = requests.post(base + "/revert", headers=blogger._h(tok), timeout=60)
            if r.status_code != 200:
                print(f"[실패] 예약 취소 실패: {title} {r.status_code} {r.text[:150]}")
                continue
        params = {}
        if when != "now":
            params["publishDate"] = dt.datetime.strptime(when, "%Y-%m-%d %H:%M").replace(tzinfo=KST).isoformat()
        r = requests.post(base + "/publish", headers=blogger._h(tok), params=params, timeout=60)
        if r.status_code == 200:
            j = r.json()
            print(f"[완료] {title} → {j.get('status')} {j.get('published')} {j.get('url')}")
        else:
            print(f"[실패] {title} {r.status_code} {r.text[:200]}")


if __name__ == "__main__":
    main()
