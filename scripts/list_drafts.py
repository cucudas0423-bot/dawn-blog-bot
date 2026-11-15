"""임시저장 글 목록을 보여주고, --publish 면 PLAN 형식(id=now;...)으로 출력해요."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blogger  # noqa: E402
from restyle_posts import all_posts  # noqa: E402
tok = blogger.access_token()
ds = [p for p in all_posts(tok) if p["_status"] == "draft"]
for p in ds:
    print(f"{p['id']}  {p.get('updated','')[:10]}  {p['title']}")
print("PLAN=" + ";".join(f"{p['id']}=now" for p in ds))
