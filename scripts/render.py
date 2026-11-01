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
HEROES = sorted(glob.glob(os.path.join(ROOT, "templates", "heroes", "*.jpg")))


def hero_photo():
    """대표 이미지 배경 사진을 날짜별로 돌려 써요. HERO=2 처럼 번호로 고를 수도 있어요."""
    if not HEROES:
        return None
    pick = os.environ.get("HERO")
    if pick and pick.isdigit() and 1 <= int(pick) <= len(HEROES):
        return HEROES[int(pick) - 1]
    import datetime as dt
    return HEROES[dt.date.today().toordinal() % len(HEROES)]


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
