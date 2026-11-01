"""Render a writeup Markdown file to a self-contained HTML and a PDF (Edge headless).

    python scripts/build_pdf.py writeup/bias_discovery.md
    python scripts/build_pdf.py writeup/documentation.md [Arnaud_TOE_Best_Documentation]

Images are embedded as base64 so the HTML is standalone; the PDF goes to writeup/pdf/, named after the
Markdown file unless a second argument gives the name.
The Zindi special-prize form accepts PDF files up to 10 MB; the script fails above that.

Layout conventions read from the Markdown:
- `<!-- CONTENTS -->` becomes a linked table of contents. Its page numbers come from a first rendering: the PDF's
  named destinations give the page of every heading, and the page is rendered again with them.
- `<!-- footer: text -->` and `<!-- author: name -->` set the running footer and the PDF metadata. Every page but
  the first gets the footer, the current section and "page / pages"; the PDF gets bookmarks for every heading.
- "Section 4.1", "Sections 6–7", "Figure 2" and "Appendix A" in running text become internal links.
- A paragraph opening with **Key finding:**, **Lesson:** or **Recommendation:** is set as a callout box.
"""
import base64
import html as htmllib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import markdown
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
FOOTER_FONT = Path(r"C:\Windows\Fonts\segoeui.ttf")
MAX_BYTES = 10 * 1024 * 1024

CSS = """
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.2pt; line-height: 1.45; color: #1b1f24; }
h1 { font-size: 17pt; margin: 0 0 6pt; color: #0b3d62; }
h2 { font-size: 13.5pt; margin: 18pt 0 6pt; color: #0b3d62; border-bottom: 1.5px solid #d5dee8; padding-bottom: 3pt; }
h2 .num { display: inline-block; min-width: 19pt; height: 19pt; line-height: 19pt; padding: 0 4pt; margin-right: 7pt;
          box-sizing: border-box; border-radius: 5pt; background: #0b3d62; color: #fff; font-size: 10.5pt;
          text-align: center; vertical-align: 1.5pt; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; color: #0b3d62; }
h3 .num { color: #2a78d6; margin-right: 5pt; }
p, li { margin: 3pt 0; }
a { color: #1f63b5; text-decoration: none; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #eef2f6; padding: 0 2px; border-radius: 2px; }
pre { background: #f3f7fb; border-left: 3px solid #2a78d6; padding: 7pt 9pt; border-radius: 0 4px 4px 0;
      font-size: 8.6pt; white-space: pre-wrap; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; margin: 7pt 0 9pt; font-size: 9pt; width: 100%; }
th { color: #0b3d62; font-weight: 600; text-align: left; border-bottom: 1.6px solid #0b3d62; padding: 4pt 5pt;
     vertical-align: bottom; }
td { border-bottom: 1px solid #dfe6ee; padding: 3.5pt 5pt; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f6f9fc; }
img { max-width: 100%; display: block; margin: 6pt auto; }
em { color: #44505c; }
figure { margin: 10pt 0 12pt; page-break-inside: avoid; }
figcaption { font-size: 8.8pt; line-height: 1.38; color: #44505c; }
.figlabel { font-weight: 600; color: #0b3d62; }
.callout { border-left: 3.5px solid #2a78d6; background: #eef5fc; padding: 6pt 10pt; margin: 8pt 0;
           border-radius: 0 5px 5px 0; page-break-inside: avoid; }
.callout.lesson { border-left-color: #eb6834; background: #fdf1eb; }
.callout.recommendation { border-left-color: #1baf7a; background: #eaf7f1; }
.pill { display: inline-block; font-size: 7.6pt; font-weight: 600; line-height: 1.3; padding: 0.4pt 5pt;
        margin: 0 4pt 1pt 0; border-radius: 7pt; white-space: nowrap; }
.pill.yes { background: #dcf2e8; color: #0d5a3e; } .pill.no { background: #e9edf2; color: #3b4651; }
.pill.hedge { background: #fde6da; color: #8a3410; }
.pill.info { background: #e1edfb; color: #0b3d62; display: table; margin: 2pt 0 2pt; }
.sep { display: none; }
h2, h3 { page-break-after: avoid; } img, pre { page-break-inside: avoid; }
table { page-break-inside: auto; } tr { page-break-inside: avoid; }
.newpage { page-break-before: always; height: 0; }
.small table { font-size: 7.8pt; } .small th, .small td { padding: 1.2pt 3pt; line-height: 1.33; } .small code { font-size: 7.3pt; }
.small td:nth-child(n+4) { white-space: nowrap; }

.cover { page-break-after: always; }
.cover .kicker { text-transform: uppercase; letter-spacing: .09em; font-size: 8.4pt; font-weight: 600;
                 color: #2a78d6; margin: 6pt 0 8pt; }
.cover h1 { font-size: 29pt; line-height: 1.1; margin: 0 0 8pt; letter-spacing: -.01em; }
.cover .subtitle { font-size: 13.5pt; line-height: 1.35; color: #44505c; margin: 0 0 12pt; }
.cover .byline { font-size: 9.6pt; color: #44505c; padding-bottom: 11pt; margin-bottom: 14pt;
                 border-bottom: 2px solid #0b3d62; }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt; margin: 0 0 14pt; }
.tile { background: #f3f7fb; border-top: 3px solid #2a78d6; border-radius: 0 0 5px 5px; padding: 7pt 8pt 8pt;
        font-size: 8.2pt; line-height: 1.33; color: #44505c; }
.tile b { display: block; font-size: 18pt; line-height: 1.1; color: #0b3d62; margin-bottom: 3pt; }
.tile br { display: none; }
.cover .lede { font-size: 10.9pt; line-height: 1.52; margin: 0 0 6pt; }
.cover .ids { font-size: 9pt; border: 1px solid #d5dee8; border-radius: 5px; padding: 7pt 10pt; margin-top: 12pt; }

.toc { margin: 0 0 10pt; }
.toc-title { font-size: 16pt; font-weight: 700; color: #0b3d62; margin: 0 0 6pt; }
.toc a { display: flex; align-items: baseline; color: #1b1f24; padding: 0.6pt 0; }
.toc .toc2 { font-weight: 600; font-size: 9.8pt; margin-top: 2.4pt; }
.toc .toc3 { font-size: 8.5pt; color: #44505c; padding-left: 22pt; }
.toc .tn { min-width: 22pt; color: #2a78d6; }
.toc .dots { flex: 1; border-bottom: 1px dotted #aab6c3; margin: 0 5pt; position: relative; top: -3pt; }
.toc .tp { min-width: 14pt; text-align: right; font-variant-numeric: tabular-nums; color: #0b3d62; }
.boxtitle { font-size: 11pt; font-weight: 700; color: #0b3d62; margin: 10pt 0 2pt; }
"""

LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
HEADING = re.compile(r'<h([23]) id="([^"]+)">(.*?)</h\1>', re.S)
NUMBERED = re.compile(r"^(\d+(?:\.\d+)?)\.?\s+(.*)$", re.S)
APPENDIX = re.compile(r"^Appendix ([A-Z])\.")
FIGURE = re.compile(r'<p><img([^>]*)>\s*<em>Figure (\d+)\.\s*(.*?)</em></p>', re.S)
CALLOUT = re.compile(r"<p><strong>(Key finding|Lesson|Recommendation):</strong>")
REF = re.compile(r"\b(Sections?|Figures?|Appendix)\s+((?:[A-Z]\b|\d+(?:\.\d+)?)(?:(?:, | and |–)\d+(?:\.\d+)?)*)")
NO_LINK = {"a", "code", "pre", "h1", "h2", "h3", "span", "title"}
TOC_MARK = "<!-- CONTENTS -->"


def embed_images(html: str, base: Path) -> str:
    def repl(m):
        src = m.group(1)
        p = (base / src).resolve()
        if not p.exists():
            raise FileNotFoundError(p)
        data = base64.b64encode(p.read_bytes()).decode()
        return f'src="data:image/png;base64,{data}"'
    return re.sub(r'src="([^"]+\.png)"', repl, html)


def separate_lists(text: str) -> str:
    """Python-Markdown needs a blank line before a list that follows a paragraph line, and 4-space indents
    for anything nested in a list item (sub-lists, continuation paragraphs, tables)."""
    out, prev = [], ""
    in_code = in_list = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        if (not in_code and LIST_ITEM.match(line) and prev.strip()
                and not LIST_ITEM.match(prev) and not prev.startswith(("|", "#"))):
            out.append("")
        lead = len(line) - len(line.lstrip(" "))
        if not in_code and line.strip():
            if LIST_ITEM.match(line):
                in_list = True
            elif lead == 0:
                in_list = False
        if not in_code and LIST_ITEM.match(line) and lead in (2, 6):
            line = " " * (lead * 2) + line.lstrip(" ")  # nested lists need 4-space indents
        elif not in_code and in_list and line.strip() and lead in (2, 3, 5):
            line = " " * {2: 4, 3: 4, 5: 6}[lead] + line.lstrip(" ")  # items under "1." are indented 3
        out.append(line)
        prev = line
    return "\n".join(out)


def plain(fragment: str) -> str:
    return htmllib.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def read_headings(body: str) -> list[dict]:
    heads = []
    for m in HEADING.finditer(body):
        inner = m.group(3).strip()
        num = NUMBERED.match(inner)
        app = APPENDIX.match(inner)
        heads.append({"level": int(m.group(1)), "id": m.group(2), "inner": inner,
                      "num": num.group(1) if num else (app.group(1) if app else ""),
                      "title": num.group(2) if num else inner, "appendix": bool(app)})
    return heads


def style_headings(body: str, heads: list[dict]) -> str:
    """Section numbers become a badge (h2) or a coloured prefix (h3)."""
    for h in heads:
        if h["appendix"] or not h["num"]:
            continue
        old = f'<h{h["level"]} id="{h["id"]}">{h["inner"]}</h{h["level"]}>'
        new = f'<h{h["level"]} id="{h["id"]}"><span class="num">{h["num"]}</span>{h["title"]}</h{h["level"]}>'
        body = body.replace(old, new, 1)
    return body


def contents(heads: list[dict], pages: dict) -> str:
    rows = []
    for h in heads:
        num, title = ("", h["inner"]) if h["appendix"] else (h["num"], h["title"])
        rows.append(f'<a class="toc{h["level"]}" href="#{h["id"]}"><span class="tn">{num}</span>'
                    f'<span class="tt">{title}</span><span class="dots"></span>'
                    f'<span class="tp">{pages.get(h["id"], "00")}</span></a>')
    return '<nav class="toc"><p class="toc-title">Contents</p>' + "".join(rows) + "</nav>"


def link_references(body: str, anchors: dict) -> str:
    """Link "Section 4.1", "Sections 6–7", "Figure 2", "Appendix A" in running text (not in code or headings),
    and keep "30 %" on one line."""
    def repl(m):
        kind = m.group(1)

        def one(t):
            target = f"fig-{t.group(0)}" if kind.startswith("Figure") else anchors.get(t.group(0))
            return f'<a href="#{target}">{t.group(0)}</a>' if target else t.group(0)
        return kind + " " + re.sub(r"[A-Z]\b|\d+(?:\.\d+)?", one, m.group(2))

    parts = re.split(r"(<[^>]+>)", body)
    depth = 0
    for i, part in enumerate(parts):
        if part.startswith("<"):
            tag = re.match(r"<(/?)(\w+)", part)
            if tag and tag.group(2).lower() in NO_LINK and not part.endswith("/>"):
                depth += -1 if tag.group(1) else 1
        elif depth == 0 and part:
            parts[i] = REF.sub(repl, re.sub(r"(\d) %", "\\1\u00a0%", part))
    return "".join(parts)


def print_pdf(html: str, html_file: Path, pdf_file: Path) -> dict:
    """Print the page with Edge and return the named destinations (heading id -> page index)."""
    html_file.write_text(html, encoding="utf-8")
    # A separate profile: with Edge already open, headless printing hands over to it and writes nothing.
    # The launcher can return before the PDF is written, so wait until its size settles.
    pdf_file.unlink(missing_ok=True)
    profile = tempfile.mkdtemp(prefix="edge_print_")
    subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--user-data-dir={profile}", f"--print-to-pdf={pdf_file}", html_file.as_uri()],
                   check=True, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    last = -1
    for _ in range(120):
        size = pdf_file.stat().st_size if pdf_file.exists() else -1
        if size > 0 and size == last:
            break
        last = size
        time.sleep(1)
    shutil.rmtree(profile, ignore_errors=True)  # Edge may still hold a file or two; the OS cleans the rest
    with pymupdf.open(pdf_file) as doc:
        return {name: dest["page"] for name, dest in doc.resolve_names().items()}


def finish(pdf_file: Path, heads: list[dict], dests: dict, title: str, footer: str, author: str) -> None:
    """Running footer (text, current section, page / pages) on every page but the cover; bookmarks; metadata."""
    doc = pymupdf.open(pdf_file)
    font = pymupdf.Font(fontfile=str(FOOTER_FONT))
    n = doc.page_count
    sections = [(dests[h["id"]], h) for h in heads if h["level"] == 2 and h["id"] in dests]
    for i, page in enumerate(doc):
        if i == 0:
            continue
        current = [h for p, h in sections if p <= i]
        label = ""
        if current:
            h = current[-1]
            label = plain(h["inner"] if h["appendix"] else f'{h["num"]} · {h["title"]}')
            label = label if len(label) <= 80 else label[:78].rstrip() + "…"
        w, y, x0 = page.rect.width, page.rect.height - 24, 42.5
        right = f"{label}     {i + 1} / {n}" if label else f"{i + 1} / {n}"
        page.draw_line((x0, y - 10), (w - x0, y - 10), color=(0.84, 0.87, 0.91), width=0.6)
        tw = pymupdf.TextWriter(page.rect, color=(0.40, 0.45, 0.51))
        tw.append((x0, y), footer, font=font, fontsize=7.6)
        tw.append((w - x0 - font.text_length(right, 7.6), y), right, font=font, fontsize=7.6)
        tw.write_text(page)
    doc.set_toc([[h["level"] - 1, plain(h["inner"]), dests[h["id"]] + 1] for h in heads if h["id"] in dests])
    doc.set_metadata({"title": title, "author": author, "subject": title, "creator": "scripts/build_pdf.py",
                      "producer": "Edge headless + PyMuPDF"})
    doc.subset_fonts()
    tmp = pdf_file.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    tmp.replace(pdf_file)


def main(md_path: str, pdf_name: str | None = None) -> int:
    md_file = (ROOT / md_path).resolve()
    source = md_file.read_text(encoding="utf-8")
    footer = (re.search(r"<!-- footer: (.*?) -->", source) or [None, ""])[1]
    author = (re.search(r"<!-- author: (.*?) -->", source) or [None, ""])[1]
    body = markdown.markdown(separate_lists(source),
                             extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html", "toc"])
    body = FIGURE.sub(r'<figure id="fig-\2"><img\1><figcaption><span class="figlabel">Figure \2.</span> \3'
                      r"</figcaption></figure>", body)
    body = CALLOUT.sub(lambda m: f'<p class="callout {m.group(1).split()[0].lower()}"><strong>{m.group(1)}:</strong>',
                       body)
    heads = read_headings(body)
    anchors = {h["num"]: h["id"] for h in heads if h["num"]}
    body = link_references(style_headings(body, heads), anchors)
    body = embed_images(body, md_file.parent)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    title = plain(h1.group(1)) if h1 else md_file.stem

    out_dir = md_file.parent / "pdf"
    out_dir.mkdir(exist_ok=True)
    html_file = out_dir / f"{md_file.stem}.html"
    pdf_file = out_dir / f"{pdf_name or md_file.stem}.pdf"

    def page_html(pages: dict) -> str:
        return (f'<!doctype html><html><head><meta charset="utf-8"><title>{htmllib.escape(title)}</title>'
                f"<style>{CSS}</style></head><body>{body.replace(TOC_MARK, contents(heads, pages))}</body></html>")

    dests = print_pdf(page_html({}), html_file, pdf_file)
    if TOC_MARK in body:
        for _ in range(3):  # the numbers can move a heading only if they change the contents' height
            pages = {k: v + 1 for k, v in dests.items()}
            dests = print_pdf(page_html(pages), html_file, pdf_file)
            if all(dests.get(h["id"]) == pages.get(h["id"], 0) - 1 for h in heads):
                break
        else:
            raise RuntimeError("table of contents page numbers did not settle")
    finish(pdf_file, heads, dests, title, footer, author)
    size = pdf_file.stat().st_size
    print(f"{pdf_file.relative_to(ROOT)}: {size / 1e6:.2f} MB, {pymupdf.open(pdf_file).page_count} pages")
    return 0 if size <= MAX_BYTES else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
