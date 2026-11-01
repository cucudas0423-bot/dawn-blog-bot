"""Blogger API v3 helper.

사용법:
  python scripts/blogger.py list            # 기존 글(발행·예약·임시저장) 제목/라벨/날짜를 JSON으로 출력
  python scripts/blogger.py whoami          # 인증 확인용: 블로그 이름 출력
"""
import json
import os
import sys

import requests

API = "https://www.googleapis.com/blogger/v3"


def access_token() -> str:
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": os.environ["BLOGGER_CLIENT_ID"],
            "client_secret": os.environ["BLOGGER_CLIENT_SECRET"],
            "refresh_token": os.environ["BLOGGER_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if r.status_code != 200:
        sys.exit(f"Google 인증 실패: {r.status_code} {r.text}")
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def blog_id() -> str:
    return os.environ.get("BLOG_ID", "7402902975921367375")


def list_posts(tok):
    out = []
    for status in ("live", "scheduled", "draft"):
        page = None
        while True:
            params = {"status": status, "view": "ADMIN", "fetchBodies": "false", "maxResults": 100}
            if page:
                params["pageToken"] = page
            r = requests.get(f"{API}/blogs/{blog_id()}/posts", headers=_h(tok), params=params, timeout=30)
            r.raise_for_status()
            j = r.json()
            for p in j.get("items", []):
                out.append({
                    "status": status,
                    "title": p.get("title"),
                    "labels": p.get("labels", []),
                    "published": p.get("published"),
                    "url": p.get("url"),
                })
            page = j.get("nextPageToken")
            if not page:
                break
    return out


def insert_post(tok, title, html, labels, draft=True):
    body = {"kind": "blogger#post", "title": title, "content": html, "labels": labels}
    r = requests.post(
        f"{API}/blogs/{blog_id()}/posts",
        headers=_h(tok),
        params={"isDraft": "true" if draft else "false"},
        json=body,
        timeout=60,
    )
    if r.status_code not in (200, 201):
        sys.exit(f"글 저장 실패: {r.status_code} {r.text}")
    return r.json()


def update_title(tok, post_id, title):
    r = requests.patch(f"{API}/blogs/{blog_id()}/posts/{post_id}", headers=_h(tok), json={"title": title}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"제목 변경 실패: {r.status_code} {r.text}")
    return r.json()


def schedule_post(tok, post_id, iso_time):
    r = requests.post(
        f"{API}/blogs/{blog_id()}/posts/{post_id}/publish",
        headers=_h(tok),
        params={"publishDate": iso_time},
        timeout=60,
    )
    if r.status_code != 200:
        sys.exit(f"예약 발행 실패: {r.status_code} {r.text}")
    return r.json()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    t = access_token()
    if cmd == "list":
        print(json.dumps(list_posts(t), ensure_ascii=False, indent=1))
    elif cmd == "whoami":
        r = requests.get(f"{API}/blogs/{blog_id()}", headers=_h(t), timeout=30)
        r.raise_for_status()
        print(r.json()["name"], r.json()["url"])
