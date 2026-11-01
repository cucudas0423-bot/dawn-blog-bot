"""그래픽을 저장소에 올리고, 본문에 스타일을 입혀 Blogger에 저장한 뒤 GitHub 이슈로 결과를 알려요.

PUBLISH_MODE (저장소 변수)
  draft    : 임시저장만 (기본값)
  schedule : PUBLISH_HOUR(기본 19시, 서울) 에 예약 발행
"""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402
from style import style  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "work")
KST = dt.timezone(dt.timedelta(hours=9))


def sh(*a, check=True):
    print("$", " ".join(a))
    return subprocess.run(a, cwd=ROOT, check=check, text=True, capture_output=True)


def push(msg):
    sh("git", "add", "-A", "images", "drafts")
    if sh("git", "diff", "--cached", "--quiet", check=False).returncode == 0:
        return
    sh("git", "commit", "-m", msg)
    for _ in range(3):
        if sh("git", "push", check=False).returncode == 0:
            return
        sh("git", "pull", "--rebase", check=False)
    sys.exit("git push 실패")


def next_slot(hour):
    now = dt.datetime.now(KST)
    t = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if t <= now + dt.timedelta(minutes=30):
        t += dt.timedelta(days=1)
    return t


def main():
    meta = json.load(open(os.path.join(W, "post.json"), encoding="utf-8"))
    body = open(os.path.join(W, "body.html"), encoding="utf-8").read()
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    today = dt.datetime.now(KST).strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-z0-9]+", "-", meta["title_en"].lower()).strip("-")[:60]

    # 1) 그래픽 PNG를 images/ 로 옮기고 push → 공개 URL
    rel = f"images/{today}-{slug}"
    os.makedirs(os.path.join(ROOT, rel), exist_ok=True)
    urls = {}
    for g in sorted(set(re.findall(r'data-g="(\d+)"', body)), key=int):
        name = f"{slug}-{g}.png"
        shutil.copy(os.path.join(W, "graphics", f"g{g}.png"), os.path.join(ROOT, rel, name))
        urls[g] = f"https://raw.githubusercontent.com/{repo}/{branch}/{rel}/{name}"
    push(f"images: {today} {slug}")

    # 2) 스타일 입혀서 Blogger 저장
    html = style(body, urls)
    tok = blogger.access_token()
    mode = os.environ.get("PUBLISH_MODE", "draft")
    labels = meta.get("labels", [])[:5]
    if mode == "now":
        # 영문 제목으로 바로 발행해 깔끔한 주소를 만든 뒤 한글 제목으로 바꿔요
        p = blogger.insert_post(tok, meta["title_en"], html, labels, draft=True)
        p = blogger.schedule_post(tok, p["id"], None)
        p = blogger.update_title(tok, p["id"], meta["title"])
        state = f"바로 발행됨 → {p.get('url', '')}"
    elif mode == "schedule":
        p = blogger.insert_post(tok, meta["title_en"], html, labels, draft=True)
        when = next_slot(int(os.environ.get("PUBLISH_HOUR", "19")))
        p = blogger.schedule_post(tok, p["id"], when.isoformat())
        p = blogger.update_title(tok, p["id"], meta["title"])
        state = f"{when:%m월 %d일 %H:%M} 예약 발행"
    else:
        p = blogger.insert_post(tok, meta["title"], html, labels, draft=True)
        state = "임시저장"
    pid = p["id"]
    edit = f"https://www.blogger.com/blog/post/edit/{blogger.blog_id()}/{pid}"

    # 3) 발행용 기록 (publish-draft 워크플로가 영문 제목→발행→한글 제목 순서로 처리)
    if mode != "now":
        os.makedirs(os.path.join(ROOT, "drafts"), exist_ok=True)
        rec = {"post_id": pid, "title": meta["title"], "title_en": meta["title_en"], "created": today, "state": state}
        json.dump(rec, open(os.path.join(ROOT, "drafts", f"{pid}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        push(f"draft record: {pid}")
    tail = ("이미 발행된 글이에요. 고칠 부분이 있으면 편집 링크에서 수정하세요." if mode == "now" else
            f"발행하려면: GitHub → Actions → **publish-draft** → Run workflow → 글 ID `{pid}` 입력.\n"
            "(영문 제목으로 먼저 발행해 깔끔한 주소를 만든 뒤 한글 제목으로 자동으로 바꿔요.)")

    # 4) 결과 알림 (GitHub 이슈 → 메일/앱 알림)
    src = "\n".join(f"- [{s.get('title','출처')}]({s.get('url','')})" for s in meta.get("sources", []))
    rej = "\n".join(f"- {r}" for r in meta.get("rejected_topics", [])) or "- (없음)"
    report = f"""## {meta['title']}

**상태:** {state}
**편집 링크:** {edit}
**글 ID:** `{pid}`

### 고른 이유
{meta.get('topic_reason','')}

### 후보였다가 뺀 주제
{rej}

### 검색 설명 (Blogger 편집기 '검색 설명' 칸에 붙여넣기)
> {meta.get('description','')}

### 확인이 필요한 부분
{meta.get('notes','') or '(없음)'}

### 출처
{src}

---
{tail}
"""
    open(os.path.join(W, "report.md"), "w", encoding="utf-8").write(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8").write(report)
    sh("gh", "issue", "create", "--title", f"[{today}] {meta['title']}", "--body-file", os.path.join(W, "report.md"), check=False)
    print(report)


if __name__ == "__main__":
    main()
