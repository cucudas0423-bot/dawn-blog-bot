"""post-now 가 성공적으로 끝나면 queue/topics.txt 의 다음 주제를 하나 꺼내 post-now 를 실행해요.
이미 post-now 가 돌고 있거나 대기 중이면 아무것도 안 해요(그 실행이 끝날 때 다시 불려요)."""
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(ROOT, "queue", "topics.txt")
REPO = os.environ["GITHUB_REPOSITORY"]


def gh(*a):
    return subprocess.run(["gh", *a], check=True, text=True, capture_output=True).stdout


me = os.environ.get("SELF_RUN_ID", "")
busy = 0
for st in ("queued", "in_progress", "pending", "waiting", "requested"):
    r = json.loads(gh("api", f"repos/{REPO}/actions/workflows/post-now.yml/runs?status={st}&per_page=10"))
    busy += sum(1 for w in r.get("workflow_runs", []) if str(w["id"]) != me)
if busy:
    print(f"post-now 가 {busy}개 진행/대기 중이라 다음 차례를 기다려요")
    raise SystemExit(0)

lines = [l for l in open(Q, encoding="utf-8").read().splitlines() if l.strip()] if os.path.exists(Q) else []
if not lines:
    print("대기열이 비었어요")
    raise SystemExit(0)
topic, rest = lines[0], lines[1:]
open(Q, "w", encoding="utf-8").write("\n".join(rest) + ("\n" if rest else ""))
subprocess.run(["git", "config", "user.name", "blog-bot"], check=True)
subprocess.run(["git", "config", "user.email", "blog-bot@users.noreply.github.com"], check=True)
subprocess.run(["git", "commit", "-am", f"queue: {topic[:40]}"], check=True)
for _ in range(3):
    if subprocess.run(["git", "push"]).returncode == 0:
        break
    subprocess.run(["git", "pull", "--rebase"])
gh("api", f"repos/{REPO}/actions/workflows/post-now.yml/dispatches", "-X", "POST", "-f", "ref=main",
   "-f", f"inputs[topic]={topic}", "-F", "inputs[publish]=false")
print(f"다음 주제 실행: {topic[:60]} (남은 {len(rest)}개)")
