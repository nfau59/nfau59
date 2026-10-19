"""给 tathr.com 概念站加购买入口（幂等，可重复运行）。

用法：python3 add-buy-links.py ~/Documents/tathr-sites/concept
做了三件事：
  1. 每个概念面板的「看图」说明后面加一个「图解卡即将开售」链接；
  2. 结尾 outro 的按钮组里加一个「图解卡 · 即将开售」按钮；
  3. styles.css 末尾追加 .buy 样式。
"""
import pathlib
import re
import sys

URL = "https://shop.tathr.com/product/concept-cards-vol1/"
MARK = "<!-- tathr-buy -->"

root = pathlib.Path(sys.argv[1]).expanduser()
html_p, css_p = root / "index.html", root / "styles.css"
html, css = html_p.read_text(), css_p.read_text()

if MARK not in html:
    link = (f'{MARK}<a class="buy" href="{URL}?utm_source=tathr&amp;utm_medium=concept&amp;utm_campaign=c{{n}}">'
            '图解卡即将开售 · 先免费看第 1 张 →</a>')
    n = 0

    def add(m):
        global n
        n += 1
        return m.group(0) + "\n      " + link.format(n=n)

    html = re.sub(r'<p class="see"[^>]*>.*?</p>', add, html, flags=re.S)
    assert n == 6, f"预期 6 个概念面板，实际找到 {n} 个"
    html = html.replace(
        '<a class="btn ghost" href="#hero">',
        f'<a class="btn" href="{URL}?utm_source=tathr&amp;utm_medium=outro">图解卡 · 即将开售 ↗</a>'
        '<a class="btn ghost" href="#hero">', 1)
    html_p.write_text(html)

if ".buy {" not in css:
    css += """
/* ---------- 购买入口 ---------- */
.buy { display: inline-block; margin-top: 14px; font-size: 13px; letter-spacing: .04em;
  color: var(--accent); text-decoration: none; border-bottom: 1px solid currentColor; padding-bottom: 2px;
  transition: opacity .3s; }
.buy:hover { opacity: .75; }
"""
    css_p.write_text(css)
print("ok")
