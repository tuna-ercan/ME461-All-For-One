"""Builds docs/All_For_One_Code_Guide.pdf (run from the project folder).

python build_pdf.py <figures folder> <output pdf>
"""
import datetime
import os
import re
import sys
from xml.sax.saxutils import escape

import matplotlib
from PIL import Image as PILImage
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Comment, Keyword, Name, Number, Operator, String, Token
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, Spacer, Table,
                                TableStyle, XPreformatted)
from reportlab.platypus.doctemplate import BaseDocTemplate, Frame, PageTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from content import FILES, SECTIONS_AFTER, SECTIONS_BEFORE   # the written text lives in content.py

FIG, OUT = sys.argv[1], sys.argv[2]

# ------------------------------------------------------------------ fonts --
fd = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
for name, f in (("Sans", "DejaVuSans.ttf"), ("Sans-Bold", "DejaVuSans-Bold.ttf"),
                ("Sans-It", "DejaVuSans-Oblique.ttf"), ("Sans-BoldIt", "DejaVuSans-BoldOblique.ttf"),
                ("Mono", "DejaVuSansMono.ttf"), ("Mono-Bold", "DejaVuSansMono-Bold.ttf"),
                ("Mono-It", "DejaVuSansMono-Oblique.ttf")):
    pdfmetrics.registerFont(TTFont(name, os.path.join(fd, f)))
from reportlab.pdfbase.pdfmetrics import registerFontFamily

registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans-It", boldItalic="Sans-BoldIt")
registerFontFamily("Mono", normal="Mono", bold="Mono-Bold", italic="Mono-It", boldItalic="Mono-Bold")

INK = colors.HexColor("#1f2328")
MUTED = colors.HexColor("#57606a")
ACCENT = colors.HexColor("#2f6fbd")
RULE = colors.HexColor("#d0d7de")
SOFT = colors.HexColor("#f6f8fa")

ST = {
    "body": ParagraphStyle("body", fontName="Sans", fontSize=9.6, leading=14, textColor=INK, spaceAfter=6),
    "small": ParagraphStyle("small", fontName="Sans", fontSize=8.2, leading=11, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="Sans", fontSize=8.4, leading=11.2, textColor=INK),
    "cellmono": ParagraphStyle("cellmono", fontName="Mono", fontSize=7.8, leading=10.5, textColor=INK),
    "h1": ParagraphStyle("h1", fontName="Sans-Bold", fontSize=19, leading=24, textColor=INK, spaceBefore=4,
                         spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Sans-Bold", fontSize=13.5, leading=18, textColor=INK, spaceBefore=12,
                         spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName="Sans-Bold", fontSize=11, leading=15, textColor=ACCENT, spaceBefore=8,
                         spaceAfter=4),
    "part": ParagraphStyle("part", fontName="Sans-Bold", fontSize=26, leading=32, textColor=ACCENT,
                           alignment=TA_CENTER),
    "caption": ParagraphStyle("caption", fontName="Sans-It", fontSize=8.2, leading=11, textColor=MUTED,
                              alignment=TA_CENTER, spaceAfter=10),
    "bullet": ParagraphStyle("bullet", fontName="Sans", fontSize=9.6, leading=13.6, textColor=INK, leftIndent=14,
                             bulletIndent=4, spaceAfter=2.5),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=7.0, leading=8.75, textColor=INK),
    "toc1": ParagraphStyle("toc1", fontName="Sans-Bold", fontSize=10.5, leading=15, leftIndent=0),
    "toc2": ParagraphStyle("toc2", fontName="Sans", fontSize=9.3, leading=12.5, leftIndent=16, textColor=INK),
}

PAGE_W, PAGE_H = A4
MARGIN = 1.7 * cm
TEXT_W = PAGE_W - 2 * MARGIN


# ---------------------------------------------------------------- markup --
def md(text):
    """Tiny markup: `code`, **bold**, *italic*; everything else escaped."""
    out = escape(text)
    out = re.sub(r"`([^`]+)`", r'<font face="Mono" size="8.6" color="#953800">\1</font>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", out)
    return out


def P(text, style="body"):
    return Paragraph(md(text), ST[style])


def bullets(items, style="bullet"):
    return [Paragraph(md(t), ST[style], bulletText="•") for t in items]


def numbered(items):
    return [Paragraph(md(t), ST["bullet"], bulletText=f"{i}.") for i, t in enumerate(items, 1)]


def table(rows, widths, header=True, mono_cols=(), font=None):
    data = []
    for r, row in enumerate(rows):
        cells = []
        for c, v in enumerate(row):
            if r == 0 and header:
                cells.append(Paragraph(f"<b>{escape(v)}</b>", ST["cell"]))
            elif c in mono_cols:
                cells.append(Paragraph(escape(v), ST["cellmono"]))
            else:
                cells.append(Paragraph(md(v), ST["cell"]))
        data.append(cells)
    t = Table(data, colWidths=[w * TEXT_W for w in widths], repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), SOFT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, MUTED)]
    t.setStyle(TableStyle(style))
    return t


def figure(name, caption, width=1.0, crop=None):
    path = os.path.join(FIG, name)
    if crop:
        im = PILImage.open(path).crop(crop)
        path = os.path.join(FIG, "crop_" + name)
        im.save(path)
    w, h = PILImage.open(path).size
    iw = TEXT_W * width
    return KeepTogether([Image(path, width=iw, height=iw * h / w), Spacer(1, 3), P(caption, "caption")])


def callout(text, color="#ddf4ff", edge="#54aeff"):
    t = Table([[Paragraph(md(text), ST["body"])]], colWidths=[TEXT_W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)),
                           ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(edge)),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


def formula(text):
    t = Table([[Paragraph(f'<font face="Mono" size="8.8">{escape(text).replace(chr(10), "<br/>")}</font>',
                          ST["body"])]],
              colWidths=[TEXT_W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SOFT), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t


# ---------------------------------------------------------- code listing --
TOKEN_COLORS = [(Comment, "#6e7781", True), (String, "#0a3069", False), (Keyword, "#cf222e", False),
                (Name.Builtin, "#8250df", False), (Name.Function, "#6639ba", False),
                (Name.Class, "#953800", False), (Number, "#0550ae", False), (Operator.Word, "#cf222e", False)]


NL = chr(10)   # newline character


def lexer_for(path):
    from pygments.lexers import BashLexer, PowerShellLexer, TextLexer
    ext = os.path.splitext(path)[1].lower()
    return {".py": PythonLexer, ".ps1": PowerShellLexer, ".sh": BashLexer}.get(ext, TextLexer)()


def colour_file(text, lexer=None):
    """Syntax-colour a whole file at once (so multi-line strings stay strings);
    returns one markup string per line."""
    lines, cur = [], []
    for ttype, value in lex(text, lexer or PythonLexer()):
        style = None
        for base, col, it in TOKEN_COLORS:
            if ttype in base:
                style = (col, it)
                break
        parts = value.split(NL)
        for k, part in enumerate(parts):
            if k:                                   # a newline inside this token: start a new line
                lines.append("".join(cur))
                cur = []
            if not part:
                continue
            v = escape(part).replace(chr(0x1F411), "[sheep emoji]")
            if style:
                col, it = style
                v = f'<font color="{col}">{"<i>" + v + "</i>" if it else v}</font>'
            cur.append(v)
    if cur:
        lines.append("".join(cur))
    return lines


def listing(path):
    text = open(path, encoding="utf-8").read().rstrip(NL)
    lines = text.split(NL)
    marked = colour_file(text + NL, lexer_for(path))
    flow = []
    chunk = 70
    for start in range(0, len(lines), chunk):
        rows = []
        for i in range(start, min(start + chunk, len(lines))):
            rows.append(f'<font color="#8c959f">{i + 1:4d}</font>  {marked[i] if i < len(marked) else ""}')
        x = XPreformatted(NL.join(rows), ST["code"])
        box = Table([[x]], colWidths=[TEXT_W])
        box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SOFT), ("BOX", (0, 0), (-1, -1), 0.4, RULE),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 3),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        flow.append(box)
    return flow, lines


def line_table(lines, entries, fname):
    """entries = [(anchor text, explanation)] in file order -> 'Lines | What happens' table."""
    starts, pos = [], 0
    for anchor, _ in entries:
        for i in range(pos, len(lines)):
            if anchor in lines[i]:
                starts.append(i)
                pos = i + 1
                break
        else:
            raise SystemExit(f"{fname}: anchor not found after line {pos}: {anchor!r}")
    rows = [["Lines", "What happens there"]]
    for k, (start, (_, text)) in enumerate(zip(starts, entries)):
        end = (starts[k + 1] if k + 1 < len(starts) else len(lines)) - 1
        while end > start and not lines[end].strip():
            end -= 1
        rows.append([f"{start + 1}" if end == start else f"{start + 1}-{end + 1}", text])
    return table(rows, [0.11, 0.89], mono_cols=(0,))


# ------------------------------------------------------------- document --
class Guide(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN + 0.3 * cm,
                         bottomMargin=MARGIN, title="All For One - Code Guide",
                         author="From The Group MeEeEe", subject="How the All For One game code works")
        frame = Frame(MARGIN, MARGIN, TEXT_W, PAGE_H - 2 * MARGIN - 0.3 * cm, id="f")
        self.addPageTemplates([PageTemplate("cover", [frame], onPage=lambda c, d: None),
                               PageTemplate("normal", [frame], onPageEnd=self.decorate)])
        self.section = ""

    def beforeDocument(self):
        self.section = ""

    def decorate(self, canv, doc):
        canv.saveState()
        canv.setFont("Sans", 7.8)
        canv.setFillColor(MUTED)
        canv.drawString(MARGIN, PAGE_H - MARGIN + 0.25 * cm, "All For One  -  Code Guide")
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 0.25 * cm, self.section)
        canv.setStrokeColor(RULE)
        canv.line(MARGIN, PAGE_H - MARGIN + 0.1 * cm, PAGE_W - MARGIN, PAGE_H - MARGIN + 0.1 * cm)
        canv.drawCentredString(PAGE_W / 2, MARGIN - 0.75 * cm, str(doc.page))
        canv.restoreState()

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and getattr(f, "_toc", None):
            level, text = f._toc
            key = f"s{self.seq.nextf('toc')}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=level > 0)
            self.notify("TOCEntry", (level, text, self.page, key))
            if level == 0:
                self.section = text


def H1(text):
    p = Paragraph(escape(text), ST["h1"])
    p._toc = (0, text)
    return p


def H2(text):
    p = Paragraph(escape(text), ST["h2"])
    p._toc = (1, text)
    return p


def H3(text):
    return Paragraph(md(text), ST["h3"])


def render(blocks):
    """content.py blocks -> flowables."""
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "h1":
            out += [PageBreak(), H1(b[1])]
        elif kind == "h2":
            out += [CondPageBreak(4 * cm), H2(b[1])]
        elif kind == "h3":
            out += [CondPageBreak(2.5 * cm), H3(b[1])]
        elif kind == "p":
            out.append(P(b[1]))
        elif kind == "ul":
            out += bullets(b[1])
        elif kind == "ol":
            out += numbered(b[1])
        elif kind == "fig":
            out.append(figure(*b[1:]))
        elif kind == "table":
            out.append(table(b[1], b[2], mono_cols=b[3] if len(b) > 3 else ()))
            out.append(Spacer(1, 8))
        elif kind == "note":
            out += [callout(b[1]), Spacer(1, 8)]
        elif kind == "warn":
            out += [callout(b[1], "#fff8c5", "#d4a72c"), Spacer(1, 8)]
        elif kind == "formula":
            out += [formula(b[1]), Spacer(1, 6)]
        elif kind == "config":
            out += config_table()
        elif kind == "space":
            out.append(Spacer(1, b[1]))
        else:
            raise SystemExit(f"unknown block {kind}")
    return out


def config_table():
    rows = [["Setting", "Value", "Meaning"]]
    pending = None
    for line in open("config.py", encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r"^([A-Z][A-Z_0-9, ]*?)\s*=\s*(.*?)(?:\s+#\s*(.*))?$", line)
        if line.startswith("# ---"):
            title = line.strip("# -")
            rows.append([f"[{title}]", "", ""])
            continue
        if not m:
            continue
        name, value, comment = m.group(1), m.group(2), m.group(3) or ""
        if value.endswith(("[", "{", "(")):
            value = "(several lines - see the listing)"
        value = value.replace("\U0001f411", "[sheep emoji]")
        rows.append([name, value[:46] + ("..." if len(value) > 46 else ""), comment])
    t = table(rows, [0.27, 0.27, 0.46], mono_cols=(0, 1))
    extra = [("BACKGROUND", (0, i), (-1, i), colors.HexColor("#eaeef2")) for i, r in enumerate(rows)
             if r[0].startswith("[")]
    t.setStyle(TableStyle(extra))
    return [t]


PILImage.open(os.path.join(FIG, "shot_game_mountain.png")).crop((30, 60, 1228, 692)).save(
    os.path.join(FIG, "crop_cover.png"))
story = []
# cover
story += [Spacer(1, 4.2 * cm), Paragraph("All For One", ParagraphStyle(
    "cover", fontName="Sans-Bold", fontSize=40, leading=48, alignment=TA_CENTER, textColor=INK)),
          Spacer(1, 0.3 * cm),
          Paragraph("Code Guide", ParagraphStyle("cover2", fontName="Sans", fontSize=22, leading=28,
                                                 alignment=TA_CENTER, textColor=ACCENT)),
          Spacer(1, 0.6 * cm),
          Paragraph("How every part of the game works - structure, data flow, physics, vision, and every file "
                    "explained block by block with its full source", ParagraphStyle(
                        "cover3", fontName="Sans", fontSize=11, leading=16, alignment=TA_CENTER, textColor=MUTED)),
          Spacer(1, 1.0 * cm),
          Image(os.path.join(FIG, "crop_cover.png"), width=TEXT_W * 0.82, height=TEXT_W * 0.82 * 632 / 1198),
          Spacer(1, 1.2 * cm),
          Paragraph("From The Group MeEeEe  -  ME461", ParagraphStyle(
              "cover4", fontName="Sans-Bold", fontSize=11, alignment=TA_CENTER, textColor=INK)),
          Spacer(1, 0.2 * cm),
          Paragraph(datetime.date.today().strftime("%d %B %Y"), ParagraphStyle(
              "cover5", fontName="Sans", fontSize=9.5, alignment=TA_CENTER, textColor=MUTED))]
from reportlab.platypus import NextPageTemplate

story += [NextPageTemplate("normal"), PageBreak(),
          Paragraph("Contents", ST["h1"])]
toc = TableOfContents()
toc.levelStyles = [ST["toc1"], ST["toc2"]]
toc.dotsMinLevel = 0
story.append(toc)

story += render(SECTIONS_BEFORE)

# file by file
story += [PageBreak(), H1("Part III - Every file, block by block")]
story += [P("Each file below starts with what it is for, then a table that walks through the file from top to "
            "bottom (the line numbers match the real file), then the complete source with its comments. Read the "
            "table next to the listing: the table says *why*, the comments in the code say *what*.")]
for fname, purpose, entries in FILES:
    lines_flow, lines = listing(fname)
    story += [CondPageBreak(7 * cm), H2(f"{fname}  ({len(lines)} lines)")]
    story += [P(purpose), line_table(lines, entries, fname), Spacer(1, 8)]
    story += [KeepTogether([Paragraph("<b>Full source</b>", ST["small"]), Spacer(1, 3), lines_flow[0]])]
    story += lines_flow[1:]

story += render(SECTIONS_AFTER)

doc = Guide(OUT)
doc.multiBuild(story)
print("wrote", OUT)
