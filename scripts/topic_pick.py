"""주제 후보 이슈 댓글을 읽고 post-now 워크플로를 실행해요."""
import json
import os
import re
import subprocess

body, comment, issue = os.environ["BODY"], os.environ["COMMENT"].strip(), os.environ["ISSUE"]
repo = os.environ["GITHUB_REPOSITORY"]


def reply(msg):
    subprocess.run(["gh", "issue", "comment", issue, "--body", msg], check=False)


m = re.search(r"<!-- topics:(.*?) -->", body, re.S)
cands = json.loads(m.group(1)) if m else []

if re.fullmatch(r"(패스|pass|skip)", comment, re.I):
    reply("알겠어요. 오늘은 쓰지 않을게요.")
    subprocess.run(["gh", "issue", "close", issue], check=False)
    raise SystemExit

publish = bool(re.search(r"(발행|바로|publish)\s*$", comment))
text = re.sub(r"\s*(발행|바로|publish)\s*$", "", comment).strip()

if re.fullmatch(r"\d", text) and 1 <= int(text) <= len(cands):
    c = cands[int(text) - 1]
    topic = f"{c['title']} — {c.get('angle', '')}"
    label = c["title"]
elif len(text) >= 4:
    topic = label = text
else:
    reply("번호(1~3)나 주제를 이해하지 못했어요. 예: `2` 또는 `2 발행` 또는 직접 주제 문장.")
    raise SystemExit

r = subprocess.run(["gh", "api", f"repos/{repo}/actions/workflows/post-now.yml/dispatches", "-X", "POST",
                    "-f", "ref=main", "-f", f"inputs[topic]={topic}",
                    "-f", f"inputs[publish]={'true' if publish else 'false'}"], capture_output=True, text=True)
if r.returncode != 0:
    reply(f"글쓰기 실행을 시작하지 못했어요: {r.stderr[:200]}")
    raise SystemExit(1)
reply(f"**{label}** 주제로 글쓰기를 시작했어요. 다 쓰면 {'바로 발행하고' if publish else '임시저장하고'} 새 이슈로 알려 드릴게요. (15~20분)")
subprocess.run(["gh", "issue", "close", issue], check=False)
