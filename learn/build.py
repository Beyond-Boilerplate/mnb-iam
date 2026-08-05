#!/usr/bin/env python3
"""Build static HTML learn site from docs/lessons/*.md."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / "docs" / "lessons"
OUT = ROOT / "learn" / "dist"
ASSETS_SRC = ROOT / "learn" / "assets"
MEDIA_SRC = ROOT / "learn" / "media"
SPECS = ROOT / "tools" / "iiq-verify" / "lesson-specs"
# Prefer learn/ copy (present in academy Docker build); fall back to studio catalog.
AUDIO_HUB_CANDIDATES = (
    ROOT / "learn" / "audio-hub.json",
    ROOT / "tools" / "podcast-studio" / "catalog" / "hub.json",
)
AUDIO_MEDIA = MEDIA_SRC / "audio"


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
  <script defer src="{root}assets/progress.js"></script>
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
      <div class="path-toggle" role="group" aria-label="Learning path">
        <button type="button" class="path-btn is-active" data-path="core" id="pathCore">Core Path</button>
        <button type="button" class="path-btn" data-path="all" id="pathAll">Show all tracks</button>
      </div>
      <p class="path-hint" id="pathHint">Entry-level: Lessons 01–50 + mid-capstones. Specialist (51–110) and Sandbox (201–250) stay hidden until you opt in.</p>
      <nav class="toc" id="toc" aria-label="Lessons">
        {toc}
      </nav>
    </aside>
    <div class="stage">
      <header class="topbar">
        <button type="button" class="menu-btn" id="menuBtn" aria-label="Open lessons">☰</button>
        <div class="crumb">{crumb}</div>
        <a class="audio-link" href="{root}audio.html">Audio</a>
        <a class="lab-link" href="https://sailpoint.lmsapp.us/identityiq/login.jsf" target="_blank" rel="noopener">Open IIQ lab ↗</a>
      </header>
      <main id="main" class="lesson" data-stem="{stem}" data-verify-mode="{verify_mode}" data-paperwork-note="{paperwork_note}">
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

    def field(name: str) -> str:
        mt = re.search(rf"\*\*{name}:\*\*\s*(.+)", text)
        if mt:
            return mt.group(1).strip()
        mt = re.search(rf"\|\s*\*\*{name}\*\*\s*\|\s*([^|]+)\|", text)
        if mt:
            return mt.group(1).strip()
        return ""

    track = field("Track")
    level = field("Level") or field("Time")
    why = ""
    mw = re.search(r"## Why this matters\n\n(.+?)(?:\n\n---|\n\n## )", text, re.S)
    if mw:
        why = mw.group(1).strip().split("\n")[0]
    if not why:
        mw = re.search(r"\*\*Why(?: \(1 line\))?:\*\*\s*(.+)", text)
        if mw:
            why = mw.group(1).strip()
    return {"title": title, "track": track, "level": level, "why": why, "text": text, "stem": path.stem}


def lesson_path_kind(stem: str) -> str:
    """core=01–50; specialist=51–110; sandbox=201–250 (Enterprise Sandbox Path)."""
    if stem.startswith("mid-") or stem in {"first-90-days", "50b-choose-your-stack"}:
        return "core"
    m = re.match(r"^(\d{2,3})[a-z]?-", stem)
    if not m:
        return "core"
    n = int(m.group(1))
    if n <= 50:
        return "core"
    if 201 <= n <= 255:
        return "sandbox"
    return "specialist"


def lesson_sort_key(stem: str) -> tuple:
    if stem == "first-90-days":
        return (-1, 0, 0, stem)
    m = re.match(r"^mid-(\d+)-", stem)
    if m:
        # After base lesson and letter inserts (08b, 16b, …)
        return (int(m.group(1)), 50, 0, stem)
    m = re.match(r"^(\d{2,3})([a-z])?-", stem)
    if m:
        n = int(m.group(1))
        letter = m.group(2)
        sub = 0 if not letter else (ord(letter) - ord("a") + 1)
        return (n, sub, 0, stem)
    return (9999, 0, 0, stem)


def lesson_num(stem: str) -> str:
    if stem == "first-90-days":
        return "90d"
    m = re.match(r"^mid-(\d+)-", stem)
    if m:
        return f"✓{m.group(1)}"
    m = re.match(r"^(\d{2,3})([a-z])?-", stem)
    if m:
        return f"{int(m.group(1)):02d}{m.group(2) or ''}"
    return stem.split("-", 1)[0].zfill(2)


def toc_badge(stem: str) -> str:
    if stem.startswith("mid-"):
        return '<span class="toc-badge toc-badge-check">checkpoint</span>'
    if re.match(r"^\d{2,3}[a-z]-", stem):
        return '<span class="toc-badge">lab+</span>'
    return ""


def load_verify_meta(stem: str) -> dict:
    """Read verifyMode / paperworkNote from lesson-spec JSON when present."""
    path = SPECS / f"{stem}.json"
    if not path.is_file():
        m = re.match(r"^(\d{3})-", stem)
        if m and 201 <= int(m.group(1)) <= 255:
            return {
                "verifyMode": "paperwork",
                "paperworkNote": "Enterprise Sandbox Path — mark binder complete when the lesson Done When criteria pass (no classic Verify specs).",
            }
        return {"verifyMode": "lab", "paperworkNote": ""}
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"verifyMode": "lab", "paperworkNote": ""}
    mode = (spec.get("verifyMode") or "lab").strip().lower()
    if spec.get("disabled") is True:
        mode = "paperwork"
    note = spec.get("paperworkNote") or ""
    if mode not in {"lab", "paperwork"}:
        mode = "lab"
    return {"verifyMode": mode, "paperworkNote": note}


def load_audio_hub() -> dict:
    for path in AUDIO_HUB_CANDIDATES:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {
        "title": "Meridian IAM Audio",
        "tagline": "Conversational IAM podcasts — concepts without the lab click-paths.",
        "hosts": {"interviewer": "Alex", "expert": "Jordan"},
        "episodes": [],
    }


def audio_episode_ready(slug: str) -> dict | None:
    mp3 = AUDIO_MEDIA / f"{slug}.mp3"
    if not mp3.is_file():
        return None
    meta: dict = {"src": f"media/audio/{slug}.mp3", "durationMin": None}
    man = AUDIO_MEDIA / f"{slug}.json"
    if man.is_file():
        try:
            data = json.loads(man.read_text(encoding="utf-8"))
            meta["durationMin"] = data.get("durationMin")
            meta["turns"] = data.get("turns")
        except (OSError, json.JSONDecodeError):
            pass
    return meta


def build_audio_page(toc: str) -> str:
    hub = load_audio_hub()
    seasons: dict[int, list[dict]] = {}
    ready_count = 0
    for ep in hub.get("episodes") or []:
        seasons.setdefault(int(ep.get("season") or 1), []).append(ep)
        if audio_episode_ready(ep["slug"]):
            ready_count += 1

    season_titles = {
        1: "Foundations — IAM & SailPoint essentials",
        2: "Lifecycle & access craft",
        3: "Security, SoD, reviews & standards",
        4: "Connectors, tooling & professional craft",
    }

    blocks: list[str] = []
    for season in sorted(seasons):
        blocks.append(f'<h2 id="season-{season}">Season {season} — {html.escape(season_titles.get(season, ""))}</h2>')
        blocks.append('<div class="audio-grid">')
        for ep in seasons[season]:
            ready = audio_episode_ready(ep["slug"])
            themes = " · ".join(ep.get("themes") or [])
            status = (
                f'~{ready["durationMin"]} min · ready'
                if ready and ready.get("durationMin")
                else ("Ready" if ready else "Coming soon")
            )
            player = ""
            if ready:
                player = (
                    f'<audio class="podcast-audio" controls preload="metadata" '
                    f'src="{html.escape(ready["src"], quote=True)}"></audio>'
                )
            else:
                player = '<p class="audio-soon">Script pipeline pending — check back after studio run.</p>'
            blocks.append(
                f'<article class="audio-card" id="{html.escape(ep["id"])}" data-ready="{"1" if ready else "0"}">'
                f'<div class="audio-card-top">'
                f'<span class="audio-ep">{html.escape(ep["id"])}</span>'
                f'<span class="audio-status">{html.escape(status)}</span>'
                f"</div>"
                f'<h3>{html.escape(ep["title"])}</h3>'
                f'<p class="audio-blurb">{html.escape(ep.get("blurb") or "")}</p>'
                f'<p class="audio-themes">{html.escape(themes)}</p>'
                f"{player}"
                f"</article>"
            )
        blocks.append("</div>")

    hosts = hub.get("hosts") or {}
    body = f"""
    <p class="eyebrow">Podcast · Alex &amp; Jordan</p>
    <h1 class="display">{html.escape(hub.get("title") or "Meridian IAM Audio")}</h1>
    <p class="lede">{html.escape(hub.get("tagline") or "")}
    Two-host conversations — interviewer <strong>{html.escape(hosts.get("interviewer", "Alex"))}</strong> and
    practitioner <strong>{html.escape(hosts.get("expert", "Jordan"))}</strong> — covering SailPoint essentials,
    IAM constructs, security posture, industry standards, and tooling options.
    Lab click-paths stay in the written lessons; this hub is for digesting the ideas.</p>
    <section class="stats" aria-label="Show snapshot">
      <div><span>{len(hub.get("episodes") or [])}</span> planned episodes</div>
      <div><span>{ready_count}</span> ready to play</div>
      <div><span>2</span> hosts</div>
      <div><span>4</span> seasons</div>
    </section>
    {"".join(blocks)}
    """
    return SHELL.format(
        title=hub.get("title") or "Audio",
        description=hub.get("tagline") or "Meridian IAM Audio",
        root="",
        toc=toc,
        crumb='<a href="index.html">Curriculum</a><span>/</span><span>Audio</span>',
        body=body,
        pager='<a class="btn primary" href="index.html">← Back to curriculum</a>',
        stem="audio",
        verify_mode="paperwork",
        paperwork_note="",
    )


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    assets_out = OUT / "assets"
    assets_out.mkdir()
    shutil.copytree(ASSETS_SRC, assets_out, dirs_exist_ok=True)
    # Podcast / screencast media (gitignored binaries; present when generated locally)
    if MEDIA_SRC.is_dir():
        media_out = OUT / "media"
        for src in MEDIA_SRC.rglob("*"):
            if not src.is_file() or src.name.startswith("."):
                continue
            if src.suffix.lower() not in {".mp3", ".mp4", ".webm", ".wav", ".json"}:
                continue
            rel = src.relative_to(MEDIA_SRC)
            dest = media_out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    numbered = [p for p in LESSONS.glob("*.md") if re.match(r"^\d{2,3}[a-z]?-", p.name)]
    extras = [
        LESSONS / "first-90-days.md",
        LESSONS / "mid-16-apps-capstone.md",
        LESSONS / "mid-34-jml-capstone.md",
        LESSONS / "mid-46-certs-capstone.md",
    ]
    # numbered already includes 08b/16b/…; keep extras for mid-* + first-90
    lesson_files = sorted(
        {p.resolve(): p for p in numbered + [e for e in extras if e.exists()]}.values(),
        key=lambda p: lesson_sort_key(p.stem),
    )
    metas = [parse_lesson_meta(p) for p in lesson_files]
    for meta in metas:
        meta["path"] = lesson_path_kind(meta["stem"])

    core_count = sum(1 for m in metas if m["path"] == "core")
    specialist_count = sum(1 for m in metas if m["path"] == "specialist")
    sandbox_count = sum(1 for m in metas if m["path"] == "sandbox")

    # Group TOC by track
    toc_parts: list[str] = []
    current_track = None
    for meta in metas:
        if meta["track"] != current_track:
            current_track = meta["track"]
            track_path = meta["path"]
            toc_parts.append(
                f'<p class="toc-track" data-path="{track_path}">{html.escape(current_track or "Lessons")}</p>'
            )
        num = lesson_num(meta["stem"])
        badge = toc_badge(meta["stem"])
        toc_parts.append(
            f'<a class="toc-item" data-path="{meta["path"]}" '
            f'data-title="{html.escape(meta["title"].lower())}" '
            f'href="{html.escape(meta["stem"])}.html">'
            f'<span class="toc-num">{num}</span>'
            f'<span class="toc-label">{html.escape(meta["title"].split("—",1)[-1].strip())}'
            f"{badge}</span></a>"
        )
    toc = "\n".join(toc_parts)

    # Index — Core Path cards first
    def card_html(meta: dict) -> str:
        num = lesson_num(meta["stem"])
        return (
            f'<a class="card" data-path="{meta["path"]}" '
            f'href="{html.escape(meta["stem"])}.html">'
            f'<span class="card-num">{num}</span>'
            f'<span class="card-body"><strong>{html.escape(meta["title"].split("—",1)[-1].strip())}</strong>'
            f'<span class="card-meta">{html.escape(meta["track"])} · {html.escape(meta["level"])}</span>'
            f'<span class="card-why">{html.escape(meta["why"][:160])}{"…" if len(meta["why"])>160 else ""}</span></span></a>'
        )

    core_cards = "".join(card_html(m) for m in metas if m["path"] == "core")
    specialist_cards = "".join(card_html(m) for m in metas if m["path"] == "specialist")
    sandbox_cards = "".join(card_html(m) for m in metas if m["path"] == "sandbox")
    start = next(m for m in metas if m["stem"].startswith("01-"))
    sandbox_start = next((m for m in metas if m["stem"].startswith("201-")), None)
    hub = load_audio_hub()
    audio_ready = sum(1 for ep in hub.get("episodes") or [] if audio_episode_ready(ep["slug"]))
    audio_planned = len(hub.get("episodes") or [])
    sandbox_cta = (
        f'<a class="btn ghost" href="{sandbox_start["stem"]}.html">Sandbox Path 201</a>'
        if sandbox_start
        else ""
    )

    index_body = f"""
    <p class="eyebrow">SailPoint IdentityIQ 8.5 · Core Path for new IIQ engineers</p>
    <h1 class="display">Govern access like a bank that expects an exam.</h1>
    <p class="lede">Interactive tutorials for <strong>Meridian National Bank</strong>. Start with the <strong>Core Path</strong> (Lessons 01–50 + mid-capstones)—HR through JML, SoD, and certifications. Specialist connector and hardening tracks stay optional until Capstone 50. After the classic 110, run the <strong>Enterprise Sandbox Path</strong> (201–250) on <code>./tools/lab/docker/up.sh --enterprise</code>. Prefer listening first? Open <a href="audio.html"><strong>Meridian IAM Audio</strong></a>.</p>
    <div class="hero-actions">
      <a class="btn primary" href="{start['stem']}.html">Start lesson 01</a>
      {sandbox_cta}
      <a class="btn ghost" href="audio.html">Listen · Audio hub</a>
      <a class="btn ghost" href="first-90-days.html">First 90 days map</a>
    </div>
    <section class="stats" aria-label="Curriculum snapshot">
      <div><span>{core_count}</span> Core Path modules</div>
      <div><span>{specialist_count}</span> specialist (opt-in)</div>
      <div><span>{sandbox_count}</span> sandbox (201–250)</div>
      <div><span>{audio_ready}/{audio_planned}</span> audio episodes</div>
    </section>
    <h2 id="path">Core Path (entry-level)</h2>
    <p class="lede-sm">TOC defaults to Core. Use <em>Show all tracks</em> for specialist (51–110) and Enterprise Sandbox (201–250).</p>
    <div class="card-grid" id="coreGrid">{core_cards}</div>
    <h2 id="specialist">Specialist tracks (51–110)</h2>
    <p class="lede-sm">Directory, JDBC, SaaS, ERP, rules, plugins, hardening — after Capstone 50.</p>
    <div class="card-grid specialist-grid" id="specialistGrid">{specialist_cards}</div>
    <h2 id="sandbox">Enterprise Sandbox Path (201–250)</h2>
    <p class="lede-sm">Production-like local estate — Mailpit, Samba, Keycloak, Portal, Gitea. Practical only; requires <code>--enterprise</code>.</p>
    <div class="card-grid specialist-grid sandbox-grid" id="sandboxGrid">{sandbox_cards}</div>
    """

    index_html = SHELL.format(
        title="Curriculum",
        description=(
            f"Meridian National Bank IdentityIQ Core Path + {specialist_count} specialist "
            f"+ {sandbox_count} sandbox modules"
        ),
        root="",
        toc=toc,
        crumb="<span>Curriculum</span>",
        body=index_body,
        pager='<a class="btn primary" href="' + start["stem"] + '.html">Begin with Lesson 01 →</a>',
        stem="index",
        verify_mode="lab",
        paperwork_note="",
    )
    (OUT / "index.html").write_text(index_html, encoding="utf-8")
    (OUT / "audio.html").write_text(build_audio_page(toc), encoding="utf-8")

    for idx, meta in enumerate(metas):
        body = md_to_html(meta["text"])
        # Lesson-to-lesson markdown links → html
        body = re.sub(r'href="(\d{2,3}[a-z]?-[^"]+)\.md"', r'href="\1.html"', body)
        body = re.sub(r'href="(mid-\d+-[^"]+)\.md"', r'href="\1.html"', body)
        body = re.sub(r'href="(first-90-days)\.md"', r'href="\1.html"', body)
        body = re.sub(r'href="(_CORE_PATH_ROADMAP)\.md"', r'href="#"', body)
        # Sibling docs in repo (not published on learn site)
        doc_map = {
            "../LOCAL_SETUP.md": "https://github.com/Beyond-Boilerplate/mnb-iam/blob/main/docs/LOCAL_SETUP.md",
            "../INFRASTRUCTURE.md": "https://github.com/Beyond-Boilerplate/mnb-iam/blob/main/docs/INFRASTRUCTURE.md",
            "../HOMELAB-CD.md": "https://github.com/Beyond-Boilerplate/mnb-iam/blob/main/docs/HOMELAB-CD.md",
            "../SSD.md": "https://github.com/Beyond-Boilerplate/mnb-iam/blob/main/docs/SSD.md",
            "../../lab-data/reference/hr-column-map.md": "https://github.com/Beyond-Boilerplate/mnb-iam/blob/main/lab-data/reference/hr-column-map.md",
        }
        for src, dst in doc_map.items():
            body = body.replace(f'href="{html.escape(src, quote=True)}"', f'href="{dst}"')
            body = body.replace(f'href="{src}"', f'href="{dst}"')

        prev_n = lesson_num(metas[idx - 1]["stem"]) if idx else ""
        next_n = lesson_num(metas[idx + 1]["stem"]) if idx < len(metas) - 1 else ""
        prev_link = (
            f'<a href="{metas[idx-1]["stem"]}.html">← {prev_n}</a>'
            if idx
            else "<span></span>"
        )
        next_link = (
            f'<a href="{metas[idx+1]["stem"]}.html">{next_n} →</a>'
            if idx < len(metas) - 1
            else "<span>Curriculum complete</span>"
        )
        vmeta = load_verify_meta(meta["stem"])
        page = SHELL.format(
            title=meta["title"],
            description=meta["why"] or meta["title"],
            root="",
            toc=toc,
            crumb=f'<a href="index.html">Curriculum</a><span>/</span><span>{html.escape(lesson_num(meta["stem"]))}</span>',
            body=body,
            pager=f'<div class="pager-row">{prev_link}{next_link}</div>',
            stem=html.escape(meta["stem"], quote=True),
            verify_mode=html.escape(vmeta["verifyMode"], quote=True),
            paperwork_note=html.escape(vmeta["paperworkNote"], quote=True),
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
        "Meridian IAM Academy static build. Serve at https://sailpoint.lmsapp.us/\n",
        encoding="utf-8",
    )
    print(f"Built {len(metas)} lessons → {OUT}")


if __name__ == "__main__":
    build()
