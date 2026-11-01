"""(처음 한 번, 내 컴퓨터에서 실행) Blogger 업로드용 refresh token 을 발급해요.

준비: Google Cloud 콘솔에서 받은 OAuth 클라이언트 JSON 파일(데스크톱 앱)을
      이 파일과 같은 폴더에 client_secret.json 이름으로 저장하세요.
실행: pip install google-auth-oauthlib
      python get_refresh_token.py
브라우저가 열리면 블로그 주인 구글 계정으로 로그인 → 허용.
화면에 나온 세 값을 GitHub 저장소의 Secrets 에 넣으면 끝이에요.
"""
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(HERE, "client_secret.json")
flow = InstalledAppFlow.from_client_secrets_file(path, scopes=["https://www.googleapis.com/auth/blogger"])
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
info = json.load(open(path))
c = info.get("installed") or info.get("web")
print("\n아래 세 값을 GitHub → Settings → Secrets and variables → Actions → New repository secret 에 넣으세요.\n")
print("BLOGGER_CLIENT_ID     =", c["client_id"])
print("BLOGGER_CLIENT_SECRET =", c["client_secret"])
print("BLOGGER_REFRESH_TOKEN =", creds.refresh_token)
