"""글 주제에 어울리는 대표 이미지 배경 사진을 골라요 (templates/heroes/heroes.json)."""
import datetime as dt
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HDIR = os.path.join(ROOT, "templates", "heroes")

LIFE = re.compile(r"요리|레시피|식재료|카페|커피|와인|위스키|하이볼|맛집|여행|단풍|가을|패션|코디|음식|디저트|칵테일")


def kind_of(text: str) -> str:
    """제목·라벨·분류 글자로 글 종류를 정해요. 애매하면 finance(현재 블로그 컨셉)."""
    return "life" if LIFE.search(text or "") else "finance"


def pool(kind: str):
    try:
        tags = json.load(open(os.path.join(HDIR, "heroes.json"), encoding="utf-8"))
    except FileNotFoundError:
        return []
    return [os.path.join(HDIR, f) for f, t in sorted(tags.items())
            if not f.startswith("_") and kind in t and os.path.exists(os.path.join(HDIR, f))]


def pick(text: str, key: str = "") -> str | None:
    """key 가 있으면 그 값으로(글 ID 등), 없으면 날짜로 돌려 골라요. 맞는 사진이 없으면 None(그린 배경)."""
    ps = pool(kind_of(text))
    if not ps:
        return None
    n = int(hashlib.md5(key.encode()).hexdigest(), 16) if key else dt.date.today().toordinal()
    return ps[n % len(ps)]
