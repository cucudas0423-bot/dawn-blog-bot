# 새벽 4시의 자동매매 — 매일 독립글 자동 작성

매일 오후 2시 50분(서울)에 GitHub 서버가 Claude Code를 실행해요. Claude는 트렌드를 조사해 주제를 고르고, 글과 그래픽을 만들어 Blogger에 **임시저장**해요. 결과는 GitHub 이슈로 알려줘요. 컴퓨터나 NAS를 켜둘 필요가 없어요.

```
매일 14:50 ─▶ 기존 글 목록 확인 ─▶ Claude: 트렌드 조사·주제 선정·자료 확인·글/그래픽 작성
          ─▶ 그래픽 PNG 렌더링(2배 해상도) ─▶ 검사 ─▶ 이미지 저장소 업로드 ─▶ Blogger 임시저장 ─▶ 이슈로 알림
```

---

## 처음 한 번 설정하기 (약 30분, 컴퓨터 필요)

### 1. GitHub 저장소 만들기
1. https://github.com/new 에서 저장소를 만들어요. 이름 예: `dawn-blog-bot`
2. **Public(공개)** 로 만들어요. 그래픽 이미지를 이 저장소에서 불러오기 때문에 공개여야 블로그에 이미지가 보여요. 비밀번호나 토큰은 Secrets에 따로 저장되니 공개돼도 안전해요.
3. 이 압축파일의 내용을 전부 올려요(`.github` 폴더 포함). 웹에서 올릴 때는 "uploading an existing file"에 폴더째 끌어다 놓으면 돼요.

### 2. Claude 구독 토큰 발급
1. 컴퓨터에 Claude Code를 설치해요. Node.js가 있다면 터미널(명령 프롬프트)에서:
   ```
   npm install -g @anthropic-ai/claude-code
   ```
2. 아래 명령을 실행하고, 브라우저가 열리면 지금 쓰는 Claude 계정으로 로그인해요.
   ```
   claude setup-token
   ```
3. 화면에 나온 긴 토큰(`sk-ant-oat...`)을 복사해 두세요.

### 3. Blogger 업로드 권한 발급 (Google Cloud, 무료)
1. https://console.cloud.google.com 에 블로그 주인 구글 계정으로 로그인 → 위쪽에서 **새 프로젝트** 만들기(이름 예: dawn-blog-bot).
2. 왼쪽 메뉴 **API 및 서비스 → 라이브러리** → `Blogger API v3` 검색 → **사용**.
3. **API 및 서비스 → OAuth 동의 화면**(Google 인증 플랫폼)
   - 사용자 유형: **외부**. 앱 이름과 이메일만 넣고 저장.
   - **대상(Audience)** 에서 게시 상태를 **프로덕션으로 푸시(앱 게시)** 해요. 테스트 상태로 두면 7일마다 인증이 끊겨요. 개인용이라 구글 심사는 받지 않아도 되고, 로그인할 때 "확인되지 않은 앱" 경고가 나오면 **고급 → 이동**을 누르면 돼요.
4. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → OAuth 클라이언트 ID**
   - 애플리케이션 유형: **데스크톱 앱** → 만들기 → **JSON 다운로드**.
5. 받은 JSON 파일을 `scripts/get_refresh_token.py` 와 같은 폴더에 `client_secret.json` 이름으로 저장하고 실행해요.
   ```
   pip install google-auth-oauthlib
   python get_refresh_token.py
   ```
   브라우저가 열리면 블로그 주인 계정으로 로그인 → 허용. 화면에 세 값이 나와요.
6. `client_secret.json` 은 GitHub에 올리지 마세요(.gitignore 처리돼 있어요).

### 4. GitHub에 비밀값 넣기
저장소 → **Settings → Secrets and variables → Actions**

**Secrets** 탭 → New repository secret 으로 4개:

| 이름 | 값 |
|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | 2단계 토큰 |
| `BLOGGER_CLIENT_ID` | 3단계 결과 |
| `BLOGGER_CLIENT_SECRET` | 3단계 결과 |
| `BLOGGER_REFRESH_TOKEN` | 3단계 결과 |

**Variables** 탭(선택, 안 넣으면 기본값):

| 이름 | 기본값 | 설명 |
|---|---|---|
| `PUBLISH_MODE` | `draft` | `draft` 임시저장 / `schedule` 자동 예약발행 |
| `PUBLISH_HOUR` | `19` | schedule 모드일 때 발행 시각(서울) |
| `CLAUDE_MODEL` | `opus` | `sonnet` 으로 바꾸면 구독 사용량을 덜 써요 |
| `BLOG_ID` | `7402902975921367375` | 블로그 ID |

### 5. 시험 실행
저장소 → **Actions** 탭 → (처음이면 "I understand… enable" 클릭) → **daily-post** → **Run workflow**.
15~25분 뒤 **Issues** 탭에 결과가 올라오고, Blogger에 임시저장 글이 생겨요.

### 6. 알림 받기
GitHub 모바일 앱을 설치하거나, 저장소 오른쪽 위 **Watch → All Activity** 를 켜면 이슈가 생길 때 메일·앱 알림이 와요.

---

## 매일 쓰는 법

- **글 확인:** 이슈의 편집 링크로 Blogger에서 글을 확인·수정해요. 이슈에 있는 검색 설명을 편집기 오른쪽 "검색 설명" 칸에 붙여 넣어요.
- **발행:** Actions → **publish-draft** → Run workflow → 이슈에 적힌 글 ID 입력
  - `now` : 바로 발행
  - `2026-11-03 19:00` : 그 시각에 예약 발행
  - 영문 제목으로 먼저 발행해 깔끔한 주소를 만든 뒤 한글 제목으로 자동으로 바꿔요. Blogger 화면에서 직접 발행하면 주소가 `blog-post_12.html` 처럼 지저분해질 수 있어요.
- **특정 주제 요청:** Actions → daily-post → Run workflow → "추가 지시" 칸에 예: `SOXL 보수와 변동성 위험 정리해줘`
- **자동 예약발행으로 전환:** Variables 에서 `PUBLISH_MODE` 를 `schedule` 로 바꾸면 매일 PUBLISH_HOUR 에 자동 발행돼요.

## 글투·디자인
- 글을 다 쓴 뒤 `humanizer/`(korean-humanizer, MIT, dotoricode)의 기준으로 AI 글투를 한 번 걷어내요. 해요체는 유지해요.
- 그래픽은 "새벽 4시" 밤·가로등 무드(`templates/card.css`, 대표 이미지 배경 `templates/hero_bg.svg`)예요.
- 예전 글의 파란 강조·주황 박스를 바꾸려면 Actions → **restyle-posts** (먼저 apply 끄고 확인 → 켜고 실행).

## 파일 구성
| 경로 | 내용 |
|---|---|
| `.github/workflows/daily-post.yml` | 매일 실행 일정과 단계 |
| `.github/workflows/publish-draft.yml` | 임시저장 글 발행 |
| `prompts/daily.md` | Claude에게 주는 작업 지시 (규칙을 바꾸려면 여기 수정) |
| `templates/card.css`, `sample_card.html` | 그래픽 디자인 |
| `examples/sample_post.html` | 글 구조·문체 예시 |
| `scripts/` | 렌더링, 검사, 스타일, Blogger 업로드 |
| `images/` | 업로드된 그래픽 (자동 생성) |
| `drafts/` | 발행 대기 글 기록 (자동 생성) |

## 참고
- 실행 1회에 구독 사용량을 꽤 써요. 한도에 걸리면 그날 실행이 실패하고, 실패 알림이 메일로 와요.
- GitHub 예약 실행은 서버 사정으로 몇 분~수십 분 늦어질 수 있어요.
- 실행 기록과 중간 파일(work/)은 Actions 실행 화면의 Artifacts 에서 14일간 내려받을 수 있어요.
