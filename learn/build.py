#!/usr/bin/env python3
"""Build static HTML learn site from docs/lessons/*.md."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / "docs" / "lessons"
OUT = ROOT / "learn" / "dist"
ASSETS_SRC = ROOT / "learn" / "assets"


def md_to_html(md: str) -> str:
    """Small Markdown subset renderer (no external deps)."""
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    in_code = False
    code_lang = ""
    code_buf: list[str] = []
    in_ul = False
    in_ol = False
    in_table = False
    table_rows: list[list[str]] = []

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def close_table():
        nonlocal in_table, table_rows
        if not in_table:
            return
        out.append('<div class="table-wrap"><table>')
        for ri, row in enumerate(table_rows):
            tag = "th" if ri == 0 else "td"
            if ri == 1 and all(re.match(r"^:?-+:?$", c.strip()) for c in row):
                continue
            out.append("<tr>" + "".join(f"<{tag}>{inline(c.strip())}</{tag}>" for c in row) + "</tr>")
        out.append("</table></div>")
        in_table = False
        table_rows = []

    def inline(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r"`([^`]+)`", r'<code>\1</code>', text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
        text = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
            text,
        )
        return text

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            close_lists()
            close_table()
            if not in_code:
                in_code = True
                code_lang = line[3:].strip()
                code_buf = []
            else:
                cls = f' class="language-{html.escape(code_lang)}"' if code_lang else ""
                out.append(f"<pre><code{cls}>{html.escape(chr(10).join(code_buf))}</code></pre>")
                in_code = False
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            close_lists()
            cells = [c for c in line.strip().strip("|").split("|")]
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            i += 1
            continue
        else:
            close_table()

        if not line.strip():
            close_lists()
            i += 1
            continue
        if line.startswith("---"):
            close_lists()
            out.append("<hr />")
            i += 1
            continue
        if line.startswith("# "):
            close_lists()
            out.append(f"<h1>{inline(line[2:])}</h1>")
            i += 1
            continue
        if line.startswith("## "):
            close_lists()
            slug = re.sub(r"[^a-z0-9]+", "-", line[3:].lower()).strip("-")
            out.append(f'<h2 id="{slug}">{inline(line[3:])}</h2>')
            i += 1
            continue
        if line.startswith("### "):
            close_lists()
            out.append(f"<h3>{inline(line[4:])}</h3>")
            i += 1
            continue
        gm = re.match(r"^- \[([ xX])\] (.*)$", line)
        if gm:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append('<ul class="goals">')
                in_ul = True
            checked = " checked" if gm.group(1).lower() == "x" else ""
            out.append(
                f'<li><label><input type="checkbox" disabled{checked} /> {inline(gm.group(2))}</label></li>'
            )
            i += 1
            continue
        if line.startswith("- "):
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line[2:])}</li>")
            i += 1
            continue
        m = re.match(r"^(\d+)\. ", line)
        if m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(line[m.end():])}</li>")
            i += 1
            continue

        close_lists()
        # Callouts used in enterprise tutorials
        stripped = line.lstrip()
        if stripped.startswith("**Expected result:**"):
            out.append(f'<p class="callout expect">{inline(line)}</p>')
        elif stripped.startswith("**If it fails:**"):
            out.append(f'<p class="callout fail">{inline(line)}</p>')
        elif stripped.startswith("**Control") or stripped.startswith("**Business:**"):
            out.append(f'<p class="callout control">{inline(line)}</p>')
        elif line.startswith("**") and ":**" in line and line.count("**") <= 4:
            out.append(f'<p class="meta-line">{inline(line)}</p>')
        else:
            out.append(f"<p>{inline(line)}</p>")
        i += 1

    close_lists()
    close_table()
    return "\n".join(out)


SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} · Meridian IAM Academy</title>
  <meta name="description" content="{description}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=IBM+Plex+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{root}assets/academy.css" />
  <script defer src="{root}assets/academy.js"></script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <div class="app">
    <aside class="rail" id="rail">
      <div class="brand">
        <a href="{root}index.html" class="brand-mark">
          <span class="vault-plate">MNB</span>
          <span class="brand-text">
            <strong>Meridian</strong>
            <em>IAM Academy</em>
          </span>
        </a>
        <button type="button" class="rail-close" id="railClose" aria-label="Close menu">×</button>
      </div>
      <label class="search">
        <span class="sr-only">Filter lessons</span>
        <input type="search" id="lessonFilter" placeholder="Filter lessons…" autocomplete="off" />
      </label>
      <nav class="toc" id="toc" aria-label="Lessons">
        {toc}
      </nav>
    </aside>
    <div class="stage">
      <header class="topbar">
        <button type="button" class="menu-btn" id="menuBtn" aria-label="Open lessons">☰</button>
        <div class="crumb">{crumb}</div>
        <a class="lab-link" href="https://sailpoint.lmsapp.us/identityiq/login.jsf" target="_blank" rel="noopener">Open IIQ lab ↗</a>
      </header>
      <main id="main" class="lesson">
        {body}
        <footer class="pager">{pager}</footer>
      </main>
    </div>
  </div>
</body>
</html>
"""


def parse_lesson_meta(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    title = path.stem
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        title = m.group(1).strip()
    track = ""
    mt = re.search(r"\*\*Track:\*\*\s*(.+)", text)
    if mt:
        track = mt.group(1).strip()
    level = ""
    ml = re.search(r"\*\*Level:\*\*\s*(.+)", text)
    if ml:
        level = ml.group(1).strip()
    why = ""
    mw = re.search(r"## Why this matters\n\n(.+?)(?:\n\n---|\n\n## )", text, re.S)
    if mw:
        why = mw.group(1).strip().split("\n")[0]
    return {"title": title, "track": track, "level": level, "why": why, "text": text, "stem": path.stem}


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    assets_out = OUT / "assets"
    assets_out.mkdir()
    shutil.copytree(ASSETS_SRC, assets_out, dirs_exist_ok=True)

    lesson_files = sorted(
        [p for p in LESSONS.glob("*.md") if re.match(r"^\d{2}-", p.name)],
        key=lambda p: p.name,
    )
    metas = [parse_lesson_meta(p) for p in lesson_files]

    # Group TOC by track
    toc_parts: list[str] = []
    current_track = None
    for meta in metas:
        if meta["track"] != current_track:
            current_track = meta["track"]
            toc_parts.append(f'<p class="toc-track">{html.escape(current_track or "Lessons")}</p>')
        num = meta["stem"][:2]
        toc_parts.append(
            f'<a class="toc-item" data-title="{html.escape(meta["title"].lower())}" href="{html.escape(meta["stem"])}.html">'
            f'<span class="toc-num">{num}</span><span class="toc-label">{html.escape(meta["title"].split("—",1)[-1].strip())}</span></a>'
        )
    toc = "\n".join(toc_parts)

    # Index
    cards = []
    for meta in metas:
        num = meta["stem"][:2]
        cards.append(
            f'<a class="card" href="{html.escape(meta["stem"])}.html">'
            f'<span class="card-num">{num}</span>'
            f'<span class="card-body"><strong>{html.escape(meta["title"].split("—",1)[-1].strip())}</strong>'
            f'<span class="card-meta">{html.escape(meta["track"])} · {html.escape(meta["level"])}</span>'
            f'<span class="card-why">{html.escape(meta["why"][:160])}{"…" if len(meta["why"])>160 else ""}</span></span></a>'
        )

    index_body = f"""
    <p class="eyebrow">SailPoint IdentityIQ 8.5 · 50 enterprise modules</p>
    <h1 class="display">Govern access like a bank that expects an exam.</h1>
    <p class="lede">Interactive technical tutorials for <strong>Meridian National Bank</strong>—authoritative HR, payment dual-control, joiner/mover/leaver, SoD, and certifications—with expected results, troubleshooting, and training-binder evidence on every lesson.</p>
    <div class="hero-actions">
      <a class="btn primary" href="{metas[0]['stem']}.html">Start lesson 01</a>
      <a class="btn ghost" href="#path">View full path</a>
    </div>
    <section class="stats" aria-label="Curriculum snapshot">
      <div><span>50</span> lessons</div>
      <div><span>9</span> tracks</div>
      <div><span>~80</span> workers in HR file</div>
      <div><span>@meridiannb.com</span> corp domain</div>
    </section>
    <h2 id="path">Learning path</h2>
    <div class="card-grid">{''.join(cards)}</div>
    """

    index_html = SHELL.format(
        title="Curriculum",
        description="Meridian National Bank IdentityIQ 50-lesson academy",
        root="",
        toc=toc,
        crumb="<span>Curriculum</span>",
        body=index_body,
        pager='<a class="btn primary" href="' + metas[0]["stem"] + '.html">Begin with Lesson 01 →</a>',
    )
    (OUT / "index.html").write_text(index_html, encoding="utf-8")

    for idx, meta in enumerate(metas):
        body = md_to_html(meta["text"])
        # Lesson-to-lesson markdown links → html
        body = re.sub(r'href="(\d{2}-[^"]+)\.md"', r'href="\1.html"', body)
        # Sibling docs in repo (not published on learn site)
        doc_map = {
            "../LOCAL_SETUP.md": "https://github.com/Beyond-Boilerplate/mnb-iam/blob/main/docs/LOCAL_SETUP.md",
            "../INFRASTRUCTURE.md": "https://github.com/Beyond-Boilerplate/mnb-iam/blob/main/docs/INFRASTRUCTURE.md",
            "../HOMELAB-CD.md": "https://github.com/Beyond-Boilerplate/mnb-iam/blob/main/docs/HOMELAB-CD.md",
        }
        for src, dst in doc_map.items():
            body = body.replace(f'href="{html.escape(src, quote=True)}"', f'href="{dst}"')
            body = body.replace(f'href="{src}"', f'href="{dst}"')

        prev_link = (
            f'<a href="{metas[idx-1]["stem"]}.html">← {metas[idx-1]["stem"][:2]}</a>'
            if idx
            else "<span></span>"
        )
        next_link = (
            f'<a href="{metas[idx+1]["stem"]}.html">{metas[idx+1]["stem"][:2]} →</a>'
            if idx < len(metas) - 1
            else "<span>Curriculum complete</span>"
        )
        page = SHELL.format(
            title=meta["title"],
            description=meta["why"] or meta["title"],
            root="",
            toc=toc,
            crumb=f'<a href="index.html">Curriculum</a><span>/</span><span>{html.escape(meta["stem"][:2])}</span>',
            body=body,
            pager=f'<div class="pager-row">{prev_link}{next_link}</div>',
        )
        # Mark active toc item
        page = page.replace(
            f'href="{meta["stem"]}.html">',
            f'href="{meta["stem"]}.html" aria-current="page">',
            1,
        )
        (OUT / f"{meta['stem']}.html").write_text(page, encoding="utf-8")

    # README copy into dist
    (OUT / "README.txt").write_text(
        "Meridian IAM Academy static build. Serve this folder at /learn on iam.lmsapp.us\n",
        encoding="utf-8",
    )
    print(f"Built {len(metas)} lessons → {OUT}")


if __name__ == "__main__":
    build()
