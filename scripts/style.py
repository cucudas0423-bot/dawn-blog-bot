"""블로그 본문 HTML에 기존 글과 같은 인라인 스타일을 입혀요."""
from bs4 import BeautifulSoup

S = {
    "p": "margin:0 0 20px;",
    "h2": "color:#1f3a68;font-size:22px;font-weight:700;line-height:1.5;margin:60px 0 24px;",
    "h3": "color:#2b2f38;font-size:18px;font-weight:700;margin:36px 0 14px;",
    "list": "margin:0 0 20px;padding-left:22px;",
    "li": "margin-bottom:10px;",
    "table": "border-collapse:collapse;font-size:15px;margin:24px 0 32px;text-align:center;width:100%;",
    "th": "background:#c4c7cc;border:1px solid #dcdfe4;padding:14px;",
    "td": "border:1px solid #dcdfe4;padding:14px;",
    "pre": "background:#f5f7fb;border:1px solid #e3e6eb;border-radius:8px;padding:16px 18px;margin:0 0 24px;"
           "font-family:Consolas,Menlo,monospace;font-size:13.5px;line-height:1.6;overflow-x:auto;white-space:pre;word-break:normal;",
    "code": "background:#f1f3f6;border-radius:4px;padding:2px 6px;font-family:Consolas,Menlo,monospace;font-size:14px;",
}


def qmark(c):
    return f'<div style="color:#c9ced8;font-family:Georgia,serif;font-size:48px;line-height:1;">{c}</div>'


def style(html: str, urls: dict) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for im in soup.find_all("img", attrs={"data-g": True}):
        url = urls[im["data-g"]]
        wrap = soup.new_tag("div", style="margin:28px 0 12px;text-align:center;")
        new = soup.new_tag("img", src=url, alt=im.get("alt", ""), width="1080",
                           style="border-radius:6px;height:auto;max-width:100%;")
        wrap.append(new)
        im.replace_with(wrap)

    for q in soup.find_all("p", class_="quote"):
        bq = BeautifulSoup(
            '<blockquote style="border:none;margin:48px 0;padding:0 8px;text-align:center;">' + qmark("“")
            + '<p style="color:#2b2f38;font-family:Georgia,\'Nanum Myeongjo\',serif;font-size:21px;font-style:italic;line-height:1.7;margin:8px 0;">'
            + q.decode_contents() + "</p>" + qmark("”") + "</blockquote>", "html.parser")
        q.replace_with(bq)

    for s in soup.find_all("span", class_=["bl", "gr"]):
        b = soup.new_tag("b")
        b["style"] = ("color:#1a56db;text-decoration:underline;text-underline-offset:4px;"
                      if "bl" in s.get("class", []) else "color:#188038;")
        b.append(BeautifulSoup(s.decode_contents(), "html.parser"))
        s.replace_with(b)

    for d in soup.find_all("div", class_="box"):
        d["style"] = "background:#fff7ef;border-radius:10px;border:1px solid #f0c9a0;margin:28px 0;padding:18px 22px;"
        ps = d.find_all("p")
        for i, p in enumerate(ps):
            p["style"] = "margin:0;" if i == len(ps) - 1 else S["p"]
    for d in soup.find_all("div", class_="faq"):
        d["style"] = "background:#f5f7fb;border-radius:10px;margin:0 0 16px;padding:18px 22px;"

    for p in soup.find_all("p"):
        cls = p.get("class", [])
        if "cat" in cls:
            p["style"] = "color:#9aa1ad;font-size:14px;margin:0 0 24px;"
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
