"""work/graphics/gN.html 을 2배 해상도 PNG(work/graphics/gN.png)로 렌더링해요.

각 HTML은 templates/card.css 를 불러 쓰는 760px 폭 카드예요.
`python scripts/render.py` 로 전체, `python scripts/render.py g2` 로 하나만 렌더링할 수 있어요.
"""
import glob
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GDIR = os.path.join(ROOT, "work", "graphics")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heroes import HDIR, pick  # noqa: E402


def hero_photo():
    """글 주제(work/post.json 제목·라벨, 본문 분류)에 맞는 배경 사진. HERO=hero2.jpg 처럼 직접 고를 수도 있어요."""
    forced = os.environ.get("HERO")
    if forced:
        f = forced if forced.endswith(".jpg") else f"hero{forced}.jpg"
        return os.path.join(HDIR, f)
    text = ""
    w = os.path.join(ROOT, "work")
    try:
        import json
        m = json.load(open(os.path.join(w, "post.json"), encoding="utf-8"))
        text = m.get("title", "") + " " + " ".join(m.get("labels", []))
    except Exception:  # noqa: BLE001
        pass
    try:
        import re
        cat = re.search(r'class="cat">([^<]*)<', open(os.path.join(w, "body.html"), encoding="utf-8").read())
        text += " " + (cat.group(1) if cat else "")
    except Exception:  # noqa: BLE001
        pass
    return pick(text)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    files = sorted(glob.glob(os.path.join(GDIR, "g*.html")))
    if only:
        files = [f for f in files if os.path.basename(f).startswith(only + ".")]
    if not files:
        print("렌더링할 그래픽이 없어요 (work/graphics/g*.html)")
        return
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 760, "height": 600}, device_scale_factor=2)
        for f in files:
            pg.goto("file://" + f)
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            photo = hero_photo()
            if photo:
                pg.evaluate("""u => { const c = document.querySelector('#card.hero');
                    if (c && !c.style.getPropertyValue('--hero')) c.style.setProperty('--hero', `url("${u}")`); }""",
                            "file://" + photo)
                pg.wait_for_load_state("networkidle")
            el = pg.query_selector("#card") or pg.query_selector("body")
            out = f[:-5] + ".png"
            el.screenshot(path=out)
            box = el.bounding_box()
            print(f"{os.path.basename(out)}  {int(box['width']*2)}x{int(box['height']*2)}")
        b.close()


if __name__ == "__main__":
    main()
