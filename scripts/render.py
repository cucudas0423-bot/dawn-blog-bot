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
            el = pg.query_selector("#card") or pg.query_selector("body")
            out = f[:-5] + ".png"
            el.screenshot(path=out)
            box = el.bounding_box()
            print(f"{os.path.basename(out)}  {int(box['width']*2)}x{int(box['height']*2)}")
        b.close()


if __name__ == "__main__":
    main()
