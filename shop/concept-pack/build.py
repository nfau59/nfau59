"""生成「概念显影 · 图解卡 第一辑」的 HTML 页面。

用法：python3 build.py && node render.js
输出：out/*.html（中间文件），render.js 再把它们渲染成 PDF 和 PNG。
"""
import math
import os
import random

import segno

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

INK = "#16150f"
MUTED = "#8f8a7d"
LINE = "#d9d3c4"
ACCENT = "#ff6a3d"
PAPER = "#f6f2e9"

CONCEPTS = [
    dict(n=1, cat="人工智能", title="神经网络", en="Neural Network",
         define="一层层「小判断」叠起来，把像素、声音这类原始信号，逐步变成「这是一只猫」这样的结论。",
         like="一间层层传话的投票屋：第一排人只看画面的局部，后面每一排只听前一排的意见再投票，最后一排喊出答案。答错了，大家就调整「该更相信谁」。",
         table=[("神经元", "屋里每一个投票的人"), ("权重", "你对某位前排同学的信任程度"),
                ("激活函数", "意见够不够强烈，值不值得举手"), ("训练 / 反向传播", "公布正确答案后，回头调整信任度")],
         note="图里每一列圆点是一排「投票人」，线越粗代表越信任。橙色那条路，是这次让大家喊出「猫」的关键意见。"),
    dict(n=2, cat="计算机", title="区块链", en="Blockchain",
         define="一本由所有人共同保存、只能往后追加的账本。每一页都记着上一页的「指纹」，改动任何一页都会被立刻发现。",
         like="全村人每人手里抄着同一本账，每写满一页，就在下一页开头抄上上一页的指纹。谁想偷偷改旧账，后面所有页的指纹都对不上，全村一对就露馅。",
         table=[("区块", "账本的一页"), ("哈希", "一页内容算出来的「指纹」"),
                ("链", "每页开头抄着上一页的指纹"), ("共识机制", "全村对账，多数人的版本算数")],
         note="有人偷改了第 2 页，它的指纹从 a3f9 变成了 b6c0，第 3 页开头抄的还是 a3f9，一对就露馅。想圆谎，就得把后面每一页都重写，还要让全村都认。"),
    dict(n=3, cat="经济", title="复利", en="Compound Interest",
         define="利息也会产生利息。增长不是一条直线，而是越往后越陡的曲线，时间是最关键的变量。",
         like="滚雪球：一开始只是手心里的小雪团，越滚越大，而新粘上的雪也会继续去粘更多的雪。坡道越长，最后的雪球越惊人。",
         table=[("本金", "最初的小雪团"), ("利率", "雪有多黏"), ("时间", "坡道有多长"), ("利滚利", "粘上的雪也继续粘雪")],
         note="同样 1 万元、年化 8%：只拿利息不再投入（单利）30 年后是 3.4 万；利滚利（复利）是 10.1 万。差距几乎都出现在后半段。"),
    dict(n=4, cat="物理", title="时空弯曲", en="Curved Spacetime",
         define="广义相对论认为，引力不是一种「拉力」，而是质量把时空压弯了，其他物体只是沿着弯曲的时空走「最直的路」。",
         like="在绷紧的蹦床中间放一个保龄球，布面凹了下去。往旁边滚一颗弹珠，它会绕着凹坑打转。不是保龄球在「拉」它，是路本身弯了。",
         table=[("时空", "绷紧的蹦床布面"), ("质量", "放在中间的保龄球"), ("引力", "弹珠顺着凹陷滚过去"), ("轨道", "弹珠在坑边一圈圈绕行")],
         note="网格是时空，中间的球是质量。质量越大，凹坑越深，绕行的弹珠（行星）就被约束得越紧。"),
    dict(n=5, cat="数学", title="傅里叶变换", en="Fourier Transform",
         define="任何复杂的波形，都可以拆成一组简单正弦波的叠加。傅里叶变换就是把「混合后的波」还原成「每种频率各有多少」。",
         like="尝一口奶昔，就能说出配方：香蕉两根、草莓一把、牛奶半杯。奶昔是混合后的信号，配方就是它的频谱。",
         table=[("信号 / 波形", "一杯奶昔"), ("频率成分", "每一种水果"), ("振幅", "每种水果放了多少"), ("傅里叶变换", "尝一口，写出配方")],
         note="上面四条是单独的正弦波（频率 1、3、5、7），最下面橙色那条是它们的总和，已经接近方波。右边的柱子就是「配方」。"),
    dict(n=6, cat="热力学", title="熵", en="Entropy",
         define="熵衡量的是「有多少种微观排列对应同一个宏观样子」。乱的排列远远多于整齐的排列，所以孤立系统总是自发地越来越乱。",
         like="房间只会越住越乱：东西「乱放」的方式有成千上万种，「整齐」的方式却只有那么几种。想恢复整齐，你必须花力气去收拾。",
         table=[("低熵", "刚收拾好的房间"), ("微观状态", "每件东西具体放在哪"), ("熵增", "乱的摆法远多于整齐的摆法"), ("做功降熵", "你花力气把房间收拾好")],
         note="左边的光点排成整齐晶格，只有极少数摆法；随着时间推移它们散开，右边这种「乱」对应的摆法多得数不清。"),
]

W, H = 640, 300


def svg(body):
    return (f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Noto Sans SC, sans-serif">{body}</svg>')


def label(x, y, text, size=13, fill=MUTED, anchor="middle", weight=400):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{text}</text>')


def ill_neural():
    rng = random.Random(7)
    out = []
    # 输入：5x5 像素格，画一个简笔猫耳朵
    pix = ["10001", "11011", "11111", "10101", "11111"]
    gx, gy, s = 30, 85, 18
    for r, row in enumerate(pix):
        for c, v in enumerate(row):
            fill = INK if v == "1" else "none"
            out.append(f'<rect x="{gx+c*s}" y="{gy+r*s}" width="{s-3}" height="{s-3}" fill="{fill}" stroke="{INK}" stroke-width="1"/>')
    out.append(label(gx + 2.5 * s, gy + 5 * s + 26, "原始像素"))
    layers = [5, 5, 4, 1]
    xs = [200, 320, 440, 560]
    pos = []
    for k, n in enumerate(layers):
        top = 150 - (n - 1) * 26
        pos.append([(xs[k], top + i * 52) for i in range(n)])
    hot = [2, 1, 2, 0]
    # 输入到第一层
    for (x, y) in pos[0]:
        out.append(f'<line x1="{gx+5*s}" y1="{gy+2.5*s}" x2="{x}" y2="{y}" stroke="{LINE}" stroke-width="1"/>')
    for k in range(len(layers) - 1):
        for i, (x1, y1) in enumerate(pos[k]):
            for j, (x2, y2) in enumerate(pos[k + 1]):
                is_hot = hot[k] == i and hot[k + 1] == j
                w = 3.4 if is_hot else rng.choice([0.6, 0.9, 1.4, 2.2])
                col = ACCENT if is_hot else INK
                op = 1 if is_hot else 0.35
                out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" opacity="{op}"/>')
    for k, layer in enumerate(pos):
        for i, (x, y) in enumerate(layer):
            on = hot[k] == i
            out.append(f'<circle cx="{x}" cy="{y}" r="{13 if k == 3 else 9}" fill="{ACCENT if on else PAPER}" stroke="{INK}" stroke-width="1.5"/>')
    out.append(label(560, 154, "猫", 13, "#fff", weight=700))
    for x, t in zip(xs, ["看局部", "认部件", "拼整体", "拍板"]):
        out.append(label(x, 290, t))
    return svg("".join(out))


def ill_chain():
    out = []
    hashes = ["0000", "a3f9", "7c21", "e58b", "19d4"]
    bw, bh, gap, y = 104, 120, 22, 80
    for i in range(5):
        x = 14 + i * (bw + gap)
        bad = i == 1
        broken = i == 2
        out.append(f'<rect x="{x+6}" y="{y+6}" width="{bw}" height="{bh}" fill="{LINE}"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="{PAPER}" stroke="{ACCENT if bad else INK}" stroke-width="{2.2 if bad else 1.5}"/>')
        out.append(label(x + 12, y + 24, f"第 {i+1} 页", 14, INK, "start", 700))
        prev = hashes[i - 1] if i else "----"
        out.append(label(x + 12, y + 52, "上页指纹", 11, MUTED, "start"))
        out.append(label(x + 12, y + 68, prev, 14, ACCENT if i == 2 else INK, "start"))
        own = "b6c0" if bad else hashes[i]
        out.append(label(x + 12, y + 94, "本页指纹", 11, MUTED, "start"))
        out.append(label(x + 12, y + 110, own, 14, ACCENT if bad else INK, "start", 700))
        if i < 4:
            ax = x + bw
            col = ACCENT if i == 1 else INK
            out.append(f'<line x1="{ax}" y1="{y+60}" x2="{ax+gap}" y2="{y+60}" stroke="{col}" stroke-width="1.6"/>')
        if broken:
            out.append(label(x + bw / 2, y + bh + 30, "指纹对不上 ✕", 13, ACCENT, weight=500))
    out.append(label(14 + bw / 2 + bw + gap, y - 18, "有人偷改了这一页", 13, ACCENT, weight=500))
    out.append(label(14 + bw / 2, y + bh + 30, "创世页", 13))
    return svg("".join(out))


def ill_compound():
    out = []
    x0, y0, x1, y1 = 60, 260, 600, 30
    ymax = 110000
    X = lambda t: x0 + (x1 - x0) * t / 30
    Y = lambda v: y0 - (y0 - y1) * v / ymax
    for v in range(0, 110001, 20000):
        out.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" stroke="{LINE}" stroke-width="1"/>')
        out.append(label(x0 - 8, Y(v) + 4, f"{v//10000} 万", 11, MUTED, "end"))
    for t in range(0, 31, 10):
        out.append(label(X(t), y0 + 22, f"{t} 年", 11))
    simple = " ".join(f"{X(t):.1f},{Y(10000*(1+0.08*t)):.1f}" for t in range(31))
    comp = " ".join(f"{X(t/2):.1f},{Y(10000*1.08**(t/2)):.1f}" for t in range(61))
    out.append(f'<polyline points="{simple}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-dasharray="5 5"/>')
    out.append(f'<polyline points="{comp}" fill="none" stroke="{ACCENT}" stroke-width="3"/>')
    for t in (0, 10, 20, 30):
        v = 10000 * 1.08 ** t
        r = 4 + 9 * (v / 100627) ** (1 / 3) * 1.6
        out.append(f'<circle cx="{X(t):.1f}" cy="{Y(v)-r-4:.1f}" r="{r:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>')
    out.append(label(X(30) - 6, Y(100627) + 26, "复利 10.1 万", 14, ACCENT, "end", 700))
    out.append(label(X(30) - 6, Y(34000) - 10, "单利 3.4 万", 13, INK, "end"))
    return svg("".join(out))


def ill_spacetime():
    out = []
    cx, cy = 320, 120
    def proj(x, z):
        r = math.hypot(x, z)
        depth = 85 / (1 + (r / 1.6) ** 2)
        return cx + x * 46 - z * 0, cy + z * 17 + depth
    n = 6
    for i in range(-n, n + 1):
        pts = " ".join("%.1f,%.1f" % proj(i, z / 4) for z in range(-4 * n, 4 * n + 1))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.55"/>')
        pts = " ".join("%.1f,%.1f" % proj(x / 4, i) for x in range(-4 * n, 4 * n + 1))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.55"/>')
    # 轨道
    orb = []
    for k in range(73):
        a = 2 * math.pi * k / 72
        x, z = 2.4 * math.cos(a), 2.4 * math.sin(a)
        px, py = proj(x, z)
        orb.append(f"{px:.1f},{py-6:.1f}")
    out.append(f'<polyline points="{" ".join(orb)}" fill="none" stroke="{ACCENT}" stroke-width="1.8" stroke-dasharray="4 4"/>')
    bx, by = proj(0, 0)
    out.append(f'<circle cx="{bx}" cy="{by-20}" r="22" fill="{INK}"/>')
    mx, my = proj(2.4 * math.cos(-0.5), 2.4 * math.sin(-0.5))
    out.append(f'<circle cx="{mx:.1f}" cy="{my-12:.1f}" r="7" fill="{ACCENT}"/>')
    out.append(label(bx, by + 34, "质量（保龄球）", 13, INK))
    out.append(label(mx + 12, my - 24, "弹珠沿着凹坑绕行", 13, ACCENT, "start", 500))
    return svg("".join(out))


def ill_fourier():
    out = []
    left, right = 20, 440
    rows = [1, 3, 5, 7]
    def wave(fn, yc, amp):
        pts = []
        for k in range(361):
            t = k / 360
            pts.append(f"{left + (right-left)*t:.1f},{yc - amp*fn(t):.1f}")
        return " ".join(pts)
    for i, h in enumerate(rows):
        yc = 30 + i * 42
        out.append(f'<polyline points="{wave(lambda t, h=h: math.sin(2*math.pi*2*h*t)/h, yc, 16)}" fill="none" stroke="{INK}" stroke-width="1.3"/>')
        out.append(label(right + 12, yc + 4, f"频率 {h}", 11, MUTED, "start"))
    out.append(f'<line x1="{left}" y1="196" x2="{right}" y2="196" stroke="{LINE}"/>')
    out.append(label(left, 214, "＋ 加起来 ＝", 12, MUTED, "start"))
    s = lambda t: sum(math.sin(2*math.pi*2*h*t)/h for h in rows)
    out.append(f'<polyline points="{wave(s, 255, 30)}" fill="none" stroke="{ACCENT}" stroke-width="2.6"/>')
    # 频谱
    bx0, by0 = 500, 240
    for i, h in enumerate(rows):
        bh = 150 / h
        out.append(f'<rect x="{bx0+i*30}" y="{by0-bh:.1f}" width="20" height="{bh:.1f}" fill="{ACCENT if i==0 else INK}"/>')
        out.append(label(bx0 + i * 30 + 10, by0 + 18, str(h), 11))
    out.append(f'<line x1="{bx0-6}" y1="{by0}" x2="{bx0+120}" y2="{by0}" stroke="{INK}"/>')
    out.append(label(bx0 + 55, 290, "配方（频谱）", 13, INK))
    return svg("".join(out))


def ill_entropy():
    rng = random.Random(3)
    out = []
    for i, (x0, title, sub) in enumerate([(30, "整齐：低熵", "只有很少几种摆法"), (350, "散开：高熵", "摆法多到数不清")]):
        out.append(f'<rect x="{x0}" y="20" width="260" height="220" fill="none" stroke="{INK}" stroke-width="1.4"/>')
        out.append(label(x0 + 130, 266, title, 14, ACCENT if i else INK, weight=700))
        out.append(label(x0 + 130, 286, sub, 12))
        for r in range(6):
            for c in range(6):
                if i == 0:
                    x, y = x0 + 30 + c * 16, 50 + r * 16
                else:
                    x, y = x0 + 14 + rng.random() * 232, 34 + rng.random() * 192
                out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{ACCENT if (r+c)%7==0 else INK}"/>')
    out.append(f'<path d="M 296 110 L 344 110" stroke="{INK}" stroke-width="1.6"/><path d="M 336 104 L 344 110 L 336 116" fill="none" stroke="{INK}" stroke-width="1.6"/>')
    out.append(label(320, 100, "时间", 12, INK))
    out.append(f'<path d="M 344 150 L 296 150" stroke="{ACCENT}" stroke-width="1.6" stroke-dasharray="4 3"/><path d="M 304 144 L 296 150 L 304 156" fill="none" stroke="{ACCENT}" stroke-width="1.6"/>')
    out.append(label(320, 172, "做功收拾", 12, ACCENT))
    return svg("".join(out))


ILLS = [ill_neural, ill_chain, ill_compound, ill_spacetime, ill_fourier, ill_entropy]

FONTS = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&'
         'family=Noto+Serif+SC:wght@600;900&family=Instrument+Serif:ital@0;1&'
         'family=JetBrains+Mono:wght@400&display=block" rel="stylesheet">')

CSS = f"""
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: {PAPER}; color: {INK}; font-family: "Noto Sans SC", sans-serif; }}
.page {{ width: 210mm; height: 297mm; padding: 14mm 15mm 12mm; position: relative; overflow: hidden;
         page-break-after: always; display: flex; flex-direction: column; }}
.page:last-child {{ page-break-after: auto; }}
.top {{ display: flex; justify-content: space-between; font-family: "JetBrains Mono", monospace;
        font-size: 8.5pt; letter-spacing: .12em; text-transform: uppercase; color: {MUTED};
        border-bottom: 1px solid {INK}; padding-bottom: 3mm; }}
.top b {{ color: {INK}; font-weight: 400; }}
.head {{ display: flex; align-items: flex-end; gap: 6mm; margin-top: 9mm; }}
.num {{ font-family: "Instrument Serif", serif; font-style: italic; font-size: 64pt; line-height: .8; color: {ACCENT}; }}
h1 {{ font-family: "Noto Serif SC", serif; font-weight: 900; font-size: 40pt; line-height: 1; letter-spacing: .02em; }}
.en {{ font-family: "Instrument Serif", serif; font-style: italic; font-size: 17pt; color: {MUTED}; margin-top: 2mm; }}
.define {{ font-size: 11.5pt; line-height: 1.75; margin-top: 6mm; max-width: 165mm; }}
.ill {{ margin-top: 6mm; border: 1px solid {LINE}; background: #fbf8f1; padding: 4mm; }}
.ill svg {{ width: 100%; height: auto; display: block; }}
.note {{ font-size: 8.8pt; color: {MUTED}; line-height: 1.6; margin-top: 2.5mm; }}
.like {{ margin-top: 6mm; display: grid; grid-template-columns: 22mm 1fr; gap: 4mm; align-items: start; }}
.like .tag {{ font-family: "Noto Serif SC", serif; font-weight: 900; font-size: 18pt; color: {ACCENT}; line-height: 1.2; }}
.like p {{ font-family: "Noto Serif SC", serif; font-weight: 600; font-size: 12.5pt; line-height: 1.8; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 6mm; font-size: 10.5pt; }}
th {{ text-align: left; font-family: "JetBrains Mono", monospace; font-weight: 400; font-size: 8pt;
      letter-spacing: .12em; color: {MUTED}; padding: 0 0 2mm; border-bottom: 1px solid {INK}; }}
td {{ padding: 2.6mm 0; border-bottom: 1px solid {LINE}; vertical-align: top; }}
td:first-child {{ width: 38%; font-weight: 700; }}
.foot {{ margin-top: auto; display: flex; justify-content: space-between; align-items: flex-end; gap: 8mm;
         border-top: 1px solid {INK}; padding-top: 3.5mm; }}
.foot .cta {{ font-size: 9.5pt; line-height: 1.6; }}
.foot .cta b {{ color: {ACCENT}; }}
.foot .small {{ font-family: "JetBrains Mono", monospace; font-size: 7.5pt; color: {MUTED}; letter-spacing: .08em; margin-top: 1.5mm; }}
.qr svg {{ width: 21mm; height: 21mm; display: block; }}
/* 封面 */
.cover {{ background: {INK}; color: {PAPER}; }}
.cover .top {{ border-color: {PAPER}; color: #8f8a7d; }}
.cover .top b {{ color: {PAPER}; }}
.cover h1 {{ font-size: 54pt; line-height: 1.12; margin-top: 30mm; color: {PAPER}; }}
.cover h1 em {{ font-style: normal; color: {ACCENT}; }}
.cover .sub {{ font-family: "Instrument Serif", serif; font-style: italic; font-size: 20pt; color: #b9b5ab; margin-top: 6mm; }}
.cover .lead {{ font-size: 11.5pt; line-height: 1.8; color: #d8d3c7; margin-top: 10mm; max-width: 150mm; }}
.toc {{ margin-top: auto; display: grid; grid-template-columns: 1fr 1fr 1fr; border-top: 1px solid #3a3830; }}
.toc div {{ padding: 5mm 0 5mm; border-bottom: 1px solid #3a3830; }}
.toc i {{ font-family: "Instrument Serif", serif; font-size: 20pt; color: {ACCENT}; }}
.toc span {{ display: block; font-family: "Noto Serif SC", serif; font-weight: 900; font-size: 15pt; margin-top: 1mm; }}
.toc small {{ font-size: 8.5pt; color: #8f8a7d; }}
.cover .foot {{ border-color: {PAPER}; margin-top: 8mm; }}
.howto h2 {{ font-family: "Noto Serif SC", serif; font-weight: 900; font-size: 24pt; margin-top: 12mm; }}
.howto ol {{ margin: 6mm 0 0 6mm; font-size: 11pt; line-height: 1.9; }}
.howto li {{ margin-bottom: 3mm; padding-left: 2mm; }}
.howto .box {{ margin-top: 10mm; border: 1px solid {INK}; padding: 6mm; font-size: 10pt; line-height: 1.8; }}
.howto .box b {{ color: {ACCENT}; }}
"""


def qr(url):
    q = segno.make(url, error="m")
    import io
    buf = io.BytesIO()
    q.save(buf, kind="svg", dark=INK, light=None, border=0, xmldecl=False, svgns=True, scale=3)
    return buf.getvalue().decode()


def concept_page(c, ill):
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in c["table"])
    url = f"https://tathr.com/#c{c['n']}"
    return f"""
<section class="page">
  <div class="top"><span><b>TATHR</b> · 概念显影 · 图解卡</span><span>{c['n']:02d} / 06 · {c['cat']}</span></div>
  <div class="head"><div class="num">{c['n']:02d}</div><div><h1>{c['title']}</h1><div class="en">{c['en']}</div></div></div>
  <p class="define">{c['define']}</p>
  <div class="ill">{ill()}</div>
  <p class="note">看图：{c['note']}</p>
  <div class="like"><div class="tag">就像</div><p>{c['like']}</p></div>
  <table><tr><th>概念</th><th>类比</th></tr>{rows}</table>
  <div class="foot">
    <div><div class="cta">扫码或打开 <b>tathr.com/#c{c['n']}</b>，亲手拨动这个概念的 3D 模型。</div>
    <div class="small">© TATHR · 仅限个人与课堂使用 · 请勿转售</div></div>
    <div class="qr">{qr(url)}</div>
  </div>
</section>"""


def cover_page():
    toc = "".join(f"<div><i>{c['n']:02d}</i><span>{c['title']}</span><small>{c['cat']} · {c['en']}</small></div>" for c in CONCEPTS)
    return f"""
<section class="page cover">
  <div class="top"><span><b>TATHR</b> · 概念显影</span><span>图解卡 · 第一辑</span></div>
  <h1>把抽象的概念，<br>做成<em>看得见</em>的东西。</h1>
  <div class="sub">Concepts, made visible · Vol. 1</div>
  <p class="lead">六个跨学科的硬核概念，每一张卡都只做三件事：一句话说清它是什么，一个你早就熟悉的日常类比，一张「概念 ↔ 类比」对照表。不用公式，先建立直觉。</p>
  <div class="toc">{toc}</div>
  <div class="foot"><div class="cta">A4 可打印 · 每张卡附二维码，扫码即可在 tathr.com 拨动对应的 3D 模型。</div></div>
</section>"""


def howto_page():
    return f"""
<section class="page howto">
  <div class="top"><span><b>TATHR</b> · 概念显影 · 图解卡</span><span>使用说明</span></div>
  <h2>怎么用这套卡</h2>
  <ol>
    <li><b>先读「就像」那一段。</b>类比是入口：先在脑子里看到投票屋、蹦床或奶昔，再回头读定义，会顺很多。</li>
    <li><b>用对照表自测。</b>遮住右边一列，看着左边的术语说出对应的类比；能说出来，就说明你真的懂了。</li>
    <li><b>扫码拨一拨。</b>每张卡右下角的二维码通往 tathr.com 上对应的交互 3D 模型，每个模型都有一个可以调节的参数。</li>
    <li><b>讲给别人听。</b>把卡片打印出来贴在书桌、教室或白板旁，用类比给别人讲一遍，是检验理解最快的办法。</li>
  </ol>
  <div class="box">
    <b>授权说明</b><br>
    购买后你可以无限次打印，用于个人学习、家庭和课堂教学。请勿转售、重新分发电子文件，或用于商业印刷。
    需要机构授权、定制概念卡或交互模型，请在 <b>shop.tathr.com</b> 留言联系。
  </div>
  <div class="foot"><div><div class="cta">更多概念正在显影中：<b>tathr.com</b></div>
    <div class="small">© 2026 TATHR · CONCEPTS MADE VISIBLE</div></div></div>
</section>"""


def doc(body, title):
    return f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>{title}</title>{FONTS}<style>{CSS}</style></head><body>{body}</body></html>"


pages = [concept_page(c, f) for c, f in zip(CONCEPTS, ILLS)]
with open(os.path.join(OUT, "bundle.html"), "w") as f:
    f.write(doc(cover_page() + "".join(pages) + howto_page(), "概念显影 · 图解卡 第一辑"))
with open(os.path.join(OUT, "cover.html"), "w") as f:
    f.write(doc(cover_page(), "封面"))
for c, p in zip(CONCEPTS, pages):
    with open(os.path.join(OUT, f"{c['n']:02d}.html"), "w") as f:
        f.write(doc(p, c["title"]))
print("ok")
