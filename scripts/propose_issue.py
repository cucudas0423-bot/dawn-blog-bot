"""work/topics.json 의 주제 후보로 GitHub 이슈를 만들어요(메일·앱 알림)."""
import json
import os
import subprocess

W = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work")
t = json.load(open(os.path.join(W, "topics.json"), encoding="utf-8"))
lines = [f"## {t.get('date', '')} 오늘의 단독글 주제 후보", ""]
for i, c in enumerate(t["candidates"], 1):
    lines += [f"### {i}. {c['title']}", f"- 각도: {c.get('angle', '')}", f"- 고른 이유: {c.get('why', '')}", ""]
lines += [
    "---",
    "**고르는 법 — 이 이슈에 댓글로 답하세요**",
    "- `1` / `2` / `3` → 그 주제로 써서 **임시저장**",
    "- `1 발행` 처럼 뒤에 `발행` → 다 쓰면 **바로 발행**",
    "- 원하는 주제를 직접 써도 돼요. 예: `SOXL 보수와 변동성 정리 발행`",
    "- `패스` → 오늘은 쓰지 않아요",
    "",
    "<!-- topics:" + json.dumps(t["candidates"], ensure_ascii=False) + " -->",
]
body = "\n".join(lines)
open(os.path.join(W, "proposal.md"), "w", encoding="utf-8").write(body)
subprocess.run(["gh", "label", "create", "topic-proposal", "--color", "C98A3C", "--force"], check=False)
subprocess.run(["gh", "issue", "create", "--title", f"[{t.get('date', '')}] 오늘 쓸 주제를 골라 주세요",
                "--label", "topic-proposal", "--body-file", os.path.join(W, "proposal.md")], check=True)
print(body)
