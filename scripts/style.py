"""블로그 본문 HTML에 기존 글과 같은 인라인 스타일을 입혀요."""
from bs4 import BeautifulSoup

S = {
    "p": "margin:0 0 20px;",
    "h2": "color:#1d2026;font-size:22px;font-weight:700;line-height:1.5;margin:60px 0 22px;",
    "h3": "color:#2b2f38;font-size:18px;font-weight:700;margin:36px 0 14px;",
    "list": "margin:0 0 20px;padding-left:22px;",
    "li": "margin-bottom:10px;",
    "table": "border-collapse:collapse;font-size:15px;margin:24px 0 32px;text-align:center;width:100%;",
    "th": "background:#f1eee8;border:1px solid #e2ddd3;padding:13px;",
    "td": "border:1px solid #e2ddd3;padding:13px;",
    "pre": "background:#f5f7fb;border:1px solid #e3e6eb;border-radius:8px;padding:16px 18px;margin:0 0 24px;"
           "font-family:Consolas,Menlo,monospace;font-size:13.5px;line-height:1.6;overflow-x:auto;white-space:pre;word-break:normal;",
    "code": "background:#f1f3f6;border-radius:4px;padding:2px 6px;font-family:Consolas,Menlo,monospace;font-size:14px;",
}


def style(html: str, urls: dict) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for im in soup.find_all("img", attrs={"data-g": True}):
        url = urls[im["data-g"]]
        wrap = soup.new_tag("div", style="margin:28px 0 12px;text-align:center;")
        new = soup.new_tag("img", src=url, alt=im.get("alt", ""), width="1080",
                           style="border-radius:4px;height:auto;max-width:100%;")
        wrap.append(new)
        im.replace_with(wrap)

    # 인용구: 큰 따옴표 장식 없이 왼쪽 선만
    for q in soup.find_all("p", class_="quote"):
        q["style"] = ("border-left:3px solid #c98a3c;color:#3a3d44;font-size:17px;line-height:1.8;"
                      "margin:36px 0;padding:4px 0 4px 18px;")
        del q["class"]

    # 예전 색깔 강조(파랑·초록)는 평범한 굵게로
    for s in soup.find_all("span", class_=["bl", "gr"]):
        b = soup.new_tag("b")
        b.append(BeautifulSoup(s.decode_contents(), "html.parser"))
        s.replace_with(b)

    for d in soup.find_all("div", class_="box"):
        d["style"] = "background:#f7f5f1;border-left:3px solid #c98a3c;margin:28px 0;padding:16px 20px;"
        ps = d.find_all("p")
        for i, p in enumerate(ps):
            p["style"] = "margin:0;" if i == len(ps) - 1 else S["p"]
    for d in soup.find_all("div", class_="faq"):
        d["style"] = "border-bottom:1px solid #ebe7df;margin:0 0 8px;padding:14px 0;"

    for p in soup.find_all("p"):
        cls = p.get("class", [])
        if "cat" in cls:
            p["style"] = "color:#9a8f80;font-size:14px;margin:0 0 24px;"
        elif "disc" in cls:
            p["style"] = "border-top:1px solid #e3e6eb;color:#9aa1ad;font-size:13px;margin:48px 0 20px;padding-top:16px;"
        elif "note" in cls:
            p["style"] = "color:#9aa1ad;font-size:14px;margin:-12px 0 20px;"
        elif not p.get("style"):
            p["style"] = S["p"]

    for tag, key in (("h2", "h2"), ("h3", "h3"), ("ul", "list"), ("ol", "list"), ("li", "li"),
                     ("table", "table"), ("th", "th"), ("td", "td"), ("pre", "pre"), ("code", "code")):
        for e in soup.find_all(tag):
            e["style"] = S[key]

    for e in soup.find_all(class_=True):
        del e["class"]

    return ('<div style="color:#2b2f38;font-size:16px;line-height:1.9;word-break:keep-all;">'
            + str(soup) + "</div>")
