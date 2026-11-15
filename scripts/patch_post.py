"""글 하나의 본문에서 문구를 바꿔요. REPL='[["옛 문구","새 문구"], ...]'  POST_ID=...
--apply 없이 실행하면 찾은 개수만 보여줘요."""
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402

tok = blogger.access_token()
pid = os.environ["POST_ID"]
if pid.startswith("http"):
    path = pid.split("blogspot.com", 1)[1]
    pid = requests.get(f"{blogger.API}/blogs/{blogger.blog_id()}/posts/bypath", headers=blogger._h(tok),
                       params={"path": path}, timeout=60).json()["id"]
    print("post id:", pid)
url = f"{blogger.API}/blogs/{blogger.blog_id()}/posts/{pid}"
p = requests.get(url, headers=blogger._h(tok), params={"view": "ADMIN"}, timeout=60).json()
html = p["content"]
import re
for kw in filter(None, os.environ.get("FIND", "").split("|")):
    for m in re.finditer(re.escape(kw), html):
        print("FOUND:", html[max(0, m.start()-200):m.end()+200].replace("\n", " "))
for old, new in json.loads(os.environ["REPL"]):
    n = html.count(old)
    print(f"{n}곳: {old[:50]}")
    html = html.replace(old, new)
if "--apply" in sys.argv:
    r = requests.patch(url, headers=blogger._h(tok), json={"content": html}, timeout=60)
    print("수정", r.status_code)
