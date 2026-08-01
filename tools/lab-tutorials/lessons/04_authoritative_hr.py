#!/usr/bin/env python3
"""Lesson 04 — Authoritative HR Source: Playwright record + TTS timeline."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import (  # noqa: E402
    HR_FILE_DOCKER,
    IIQ_BASE,
    OUT,
    VIEWPORT,
)
from common.iiq_login import login  # noqa: E402
from common.overlays import (  # noqa: E402
    clear_overlays,
    hide_banner,
    hide_title_card,
    point_at,
    show_banner,
    show_title_card,
)
from common.tts import synthesize_segments, write_timeline  # noqa: E402

STEPS: list[dict[str, Any]] = [
    {
        "id": "01-title",
        "step": "Lesson 04",
        "callout": "Authoritative HR Source — Meridian National Bank",
        "narration": (
            "Welcome to Lesson 4, Authoritative H R Source. "
            "In this lab we build the Meridian H R application in Identity I Q, "
            "point it at the Docker lab file, mark it authoritative, "
            "run Aggregate M N B H R, and verify identity cubes."
        ),
    },
    {
        "id": "02-login",
        "step": "Task 2 prep",
        "callout": "Log in as spadmin",
        "narration": "First, sign in to Identity I Q as spadmin — the lab administrator account.",
    },
    {
        "id": "03-apps",
        "step": "Task 2",
        "callout": "Applications → Application Definition → Add New Application",
        "narration": (
            "Open Application Definition and choose Add New Application. "
            "We will create a Delimited File connector named M N B dash H R."
        ),
    },
    {
        "id": "04-type-name",
        "step": "Task 2",
        "callout": "Type = DelimitedFile · Name = MNB-HR",
        "narration": (
            "Set the application type to Delimited File — treat the feed as C S V — "
            "and name the application M N B dash H R."
        ),
    },
    {
        "id": "05-file",
        "step": "Task 2",
        "callout": "File path = /opt/iiq-lab-data/HRApplications.txt (Docker path)",
        "narration": (
            "For the Docker lab, the file path is slash opt slash i i q dash lab dash data "
            "slash H R Applications dot txt — not your Mac home directory. "
            "Use comma delimiter and enable has header."
        ),
    },
    {
        "id": "06-authoritative",
        "step": "Task 4",
        "callout": "Authoritative Application = ON (on the app, not the task)",
        "narration": (
            "Enable Authoritative Application on M N B dash H R itself. "
            "This flag lives on the application — not on the aggregation task — "
            "so H R can create identity cubes."
        ),
    },
    {
        "id": "07-schema",
        "step": "Task 3",
        "callout": "Discover schema · Identity attribute = userId",
        "narration": (
            "Discover the schema from the file header, then set the account identity attribute "
            "to user I D — the stable Meridian associate key."
        ),
    },
    {
        "id": "08-save-app",
        "step": "Task 2–4",
        "callout": "Save MNB-HR",
        "narration": "Save the application. M N B dash H R is now Meridian’s authoritative workforce source.",
    },
    {
        "id": "09-task",
        "step": "Task 5",
        "callout": "Create Account Aggregation task: Aggregate MNB-HR",
        "narration": (
            "Create a new Account Aggregation task named Aggregate M N B dash H R, "
            "select the M N B dash H R application, save, and run it now."
        ),
    },
    {
        "id": "10-task-result",
        "step": "Task 5",
        "callout": "Wait for Task Result → Success",
        "narration": (
            "Open the task result and wait for success. "
            "You should see roughly seventy to eighty accounts from the H R file. "
            "Aggregation creates links and cubes; attribute promotion still needs an Identity Refresh in Lesson 6."
        ),
    },
    {
        "id": "11-identities",
        "step": "Task 6",
        "callout": "Identities → verify HR cubes (e.g. Helen Ross / MNB00001)",
        "narration": (
            "Search the identity warehouse for leadership and wire personas. "
            "With user I D as the native identity, cubes may show as display names like Helen Ross "
            "while the H R account native identity is M N B zero zero zero zero one. "
            "Confirm the M N B dash H R account on the cube."
        ),
    },
    {
        "id": "12-end",
        "step": "Done",
        "callout": "Next: Lesson 06 — Refresh promotes Link attributes onto cubes",
        "narration": (
            "Lesson 4 complete. Next, Lesson 6 runs Identity Refresh tasks so H R link attributes "
            "promote onto the identity cubes. Thanks for watching."
        ),
    },
]


def _console(cmd: str, timeout: int = 180) -> str:
    import subprocess

    from common import IIQ_DOCKER_CONTAINER

    proc = subprocess.run(
        [
            "docker",
            "exec",
            IIQ_DOCKER_CONTAINER,
            "sh",
            "-c",
            "cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin && "
            f"./iiq console iiqBeans -c {json.dumps(cmd)}",
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return (proc.stdout or "") + (proc.stderr or "")


def _import_xml(path: Path) -> str:
    import subprocess
    import tempfile

    from common import IIQ_DOCKER_CONTAINER, ROOT

    xml = path.read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as f:
        f.write(xml)
        local = f.name
    remote = f"/tmp/{Path(local).name}"
    subprocess.run(["docker", "cp", local, f"{IIQ_DOCKER_CONTAINER}:{remote}"], check=True)
    return _console(f"import {remote}")


AGG_TASK_XML = """<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE TaskDefinition PUBLIC "sailpoint.dtd" "sailpoint.dtd">
<TaskDefinition formPath="/monitor/tasks/accountAggregationTask.xhtml" name="Aggregate MNB-HR" resultAction="Rename" subType="task_item_type_acct_aggregation" type="AccountAggregation">
  <Attributes>
    <Map>
      <entry key="applications" value="MNB-HR"/>
      <entry key="noOptimizeReaggregation" value="true"/>
      <entry key="promoteManagedAttributes" value="true"/>
    </Map>
  </Attributes>
  <Description>Lesson 04 Aggregate MNB-HR</Description>
  <Owner>
    <Reference class="sailpoint.object.Identity" name="spadmin"/>
  </Owner>
  <Parent>
    <Reference class="sailpoint.object.TaskDefinition" name="Account Aggregation"/>
  </Parent>
</TaskDefinition>
"""


def _ensure_agg_task_and_run() -> None:
    """Best-effort: import Aggregate MNB-HR task XML and run it via console."""
    import tempfile
    from pathlib import Path as P

    from common import ROOT

    # Prefer committed Application XML so file path / schema are correct if UI save was partial
    app_xml = ROOT / "config" / "Application" / "MNB-Application-HR.xml"
    if app_xml.exists():
        _import_xml(app_xml)
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as f:
        f.write(AGG_TASK_XML)
        tmp = P(f.name)
    _import_xml(tmp)
    _console('run Task "Aggregate MNB-HR"', timeout=300)


def _js_click(page: Page, selector: str) -> bool:
    return bool(
        page.evaluate(
            """(sel) => {
              const el = document.querySelector(sel);
              if (!el) return false;
              el.scrollIntoView({block:'center'});
              el.click();
              return true;
            }""",
            selector,
        )
    )


def _force_fill(page: Page, selector: str, value: str) -> None:
    loc = page.locator(selector).first
    loc.wait_for(state="attached", timeout=30_000)
    loc.evaluate(
        """(el, value) => {
          el.scrollIntoView({block:'center'});
          el.focus();
          el.value = value;
          el.dispatchEvent(new Event('input', {bubbles:true}));
          el.dispatchEvent(new Event('change', {bubbles:true}));
        }""",
        value,
    )


def _check_by_label(page: Page, label_substr: str) -> None:
    cbs = page.locator("input[type=checkbox]")
    n = cbs.count()
    for i in range(n):
        cb = cbs.nth(i)
        label = cb.evaluate(
            """el => {
              const lab = el.id && document.querySelector('label[for=\"'+el.id+'\"]');
              if (lab) return lab.innerText;
              return (el.parentElement && el.parentElement.innerText) || '';
            }"""
        )
        if label_substr.lower() in (label or "").lower():
            if not cb.is_checked():
                cb.evaluate("el => { el.scrollIntoView({block:'center'}); el.click(); }")
            return
    # Fallback: Authoritative often has unstable id
    page.locator("text=Authoritative Application").first.click(timeout=5_000)


def _dwell(page: Page, ms: int) -> None:
    page.wait_for_timeout(ms)


def _mark(timeline: list[dict[str, Any]], step: dict[str, Any], t0: float, extra: dict | None = None) -> None:
    entry = {
        "id": step["id"],
        "step": step["step"],
        "callout": step["callout"],
        "narration": step["narration"],
        "videoStartMs": int((time.monotonic() - t0) * 1000),
    }
    if extra:
        entry.update(extra)
    timeline.append(entry)


def run(out_dir: Path, headless: bool = True, slow_mo: int = 0) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    video_dir = out_dir / "video"
    audio_dir = out_dir / "audio"
    video_dir.mkdir(exist_ok=True)
    audio_dir.mkdir(exist_ok=True)

    timeline: list[dict[str, Any]] = []
    fail_shot = out_dir / "failure.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo or 0)
        context = browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(video_dir),
            record_video_size=VIEWPORT,
        )
        page = context.new_page()
        page.set_default_timeout(60_000)
        t0 = time.monotonic()

        try:
            # --- Title ---
            page.goto(f"{IIQ_BASE}/login.jsf", wait_until="domcontentloaded")
            show_title_card(
                page,
                "Lesson 04 — Authoritative HR Source",
                "Build MNB-HR · Aggregate · Verify cubes",
            )
            _mark(timeline, STEPS[0], t0)
            _dwell(page, 4500)
            hide_title_card(page)

            # --- Login ---
            show_banner(page, STEPS[1]["step"], STEPS[1]["callout"])
            _mark(timeline, STEPS[1], t0)
            login(page)
            show_banner(page, STEPS[1]["step"], "Signed in — home dashboard")
            _dwell(page, 2000)

            # --- Apps list / Add New ---
            show_banner(page, STEPS[2]["step"], STEPS[2]["callout"])
            _mark(timeline, STEPS[2], t0)
            page.goto(f"{IIQ_BASE}/define/applications/applications.jsf", wait_until="domcontentloaded")
            _dwell(page, 1500)
            add_btn = page.locator("#newApplicationBtn-btnEl")
            point_at(page, add_btn)
            _dwell(page, 1200)
            add_btn.click()
            page.wait_for_url("**/application.jsf**", timeout=60_000)
            _dwell(page, 1500)

            # --- Type + name ---
            show_banner(page, STEPS[3]["step"], STEPS[3]["callout"])
            _mark(timeline, STEPS[3], t0)
            page.select_option("#editForm\\:connector", label="DelimitedFile")
            _dwell(page, 2500)
            _force_fill(page, "#editForm\\:appName", "MNB-HR")
            point_at(page, page.locator("#editForm\\:appName"))
            _dwell(page, 1500)

            # --- File path (Configuration tab often holds connector settings) ---
            show_banner(page, STEPS[4]["step"], STEPS[4]["callout"])
            _mark(timeline, STEPS[4], t0)
            for tab in ("Configuration", "Details"):
                tloc = page.get_by_role("tab", name=tab)
                if tloc.count() == 0:
                    tloc = page.locator(f"a:has-text('{tab}'), li:has-text('{tab}')").first
                try:
                    tloc.first.click(timeout=3_000)
                    _dwell(page, 1200)
                except Exception:
                    pass
            page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
            _dwell(page, 800)
            file_inp = page.locator('input[name$="filename_"]').first
            if file_inp.count():
                file_inp.evaluate("el => el.scrollIntoView({block:'center'})")
                _dwell(page, 500)
                _force_fill(page, 'input[name$="filename_"]', HR_FILE_DOCKER)
            delim = page.locator('input[name$="delimiter_"]')
            if delim.count():
                _force_fill(page, 'input[name$="delimiter_"]', ",")
            page.evaluate(
                """() => {
                  const labels = [...document.querySelectorAll('td,label,span,div')];
                  for (const el of labels) {
                    const t = (el.textContent || '').trim();
                    if (/has\\s*header/i.test(t) && t.length < 40) {
                      const row = el.closest('tr') || el.parentElement;
                      const cb = row && row.querySelector('input[type=checkbox]');
                      if (cb && !cb.checked) { cb.click(); return true; }
                    }
                  }
                  return false;
                }"""
            )
            if file_inp.count():
                point_at(page, file_inp)
            _dwell(page, 2500)

            # --- Authoritative ---
            show_banner(page, STEPS[5]["step"], STEPS[5]["callout"])
            _mark(timeline, STEPS[5], t0)
            for sel in (
                'a[role="tab"]:has-text("Details")',
                "text=Details",
                "li:has-text('Details')",
            ):
                try:
                    page.locator(sel).first.click(timeout=2_000)
                    break
                except Exception:
                    continue
            _dwell(page, 800)
            page.evaluate("window.scrollTo(0, 0)")
            _dwell(page, 500)
            try:
                auth = page.get_by_text("Authoritative Application", exact=False).first
                point_at(page, auth)
                _dwell(page, 800)
                _check_by_label(page, "Authoritative Application")
            except Exception:
                page.evaluate(
                    """() => {
                      const nodes = [...document.querySelectorAll('label,td,span,div')];
                      for (const n of nodes) {
                        if (/Authoritative Application/i.test(n.textContent||'')) {
                          const row = n.closest('tr') || n.parentElement;
                          const cb = row && row.querySelector('input[type=checkbox]');
                          if (cb && !cb.checked) cb.click();
                          return;
                        }
                      }
                    }"""
                )
            _dwell(page, 1500)

            # --- Schema discover + identity attr ---
            show_banner(page, STEPS[6]["step"], STEPS[6]["callout"])
            _mark(timeline, STEPS[6], t0)
            hide_banner(page)  # banner can block bottom schema controls
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            _dwell(page, 800)
            clicked = _js_click(page, 'button[id*="discoverButton"]') or _js_click(
                page, 'input[id*="discoverButton"]'
            )
            if clicked:
                _dwell(page, 6000)
            show_banner(page, STEPS[6]["step"], STEPS[6]["callout"])
            page.evaluate(
                """() => {
                  const selects = [...document.querySelectorAll('select')];
                  for (const s of selects) {
                    const hit = [...s.options].findIndex(o => (o.text||o.value||'').trim() === 'userId');
                    if (hit >= 0 && s.options.length > 5) {
                      s.selectedIndex = hit;
                      s.dispatchEvent(new Event('change', {bubbles:true}));
                      return 'ok';
                    }
                  }
                  return 'none';
                }"""
            )
            _dwell(page, 2000)

            # --- Save app ---
            show_banner(page, STEPS[7]["step"], STEPS[7]["callout"])
            _mark(timeline, STEPS[7], t0)
            hide_banner(page)
            try:
                save = page.locator("#editForm\\:saveAppBtn")
                point_at(page, save)
                _dwell(page, 800)
                save.click(timeout=10_000)
                _dwell(page, 4000)
            except Exception:
                show_banner(page, STEPS[7]["step"], "Save click flaky — importing durable MNB-HR XML")
                _dwell(page, 1500)
            try:
                page.goto(f"{IIQ_BASE}/define/applications/applications.jsf", wait_until="domcontentloaded")
                _dwell(page, 2000)
            except Exception:
                pass
            show_banner(page, STEPS[7]["step"], "MNB-HR ready")
            _dwell(page, 2000)

            # --- Aggregation task (UI walk + console ensure) ---
            show_banner(page, STEPS[8]["step"], STEPS[8]["callout"])
            _mark(timeline, STEPS[8], t0)
            page.goto(f"{IIQ_BASE}/monitor/tasks/viewTasks.jsf?resetTab=true", wait_until="domcontentloaded")
            _dwell(page, 2500)
            for sel in [
                "text=Add New Task",
                "#newTaskBtn-btnEl",
                "a:has-text('New Task')",
                "button:has-text('New')",
            ]:
                loc = page.locator(sel)
                if loc.count():
                    try:
                        point_at(page, loc.first)
                        _dwell(page, 600)
                        loc.first.click(timeout=5_000)
                        _dwell(page, 2000)
                    except Exception:
                        pass
                    break
            show_banner(
                page,
                STEPS[8]["step"],
                "Ensuring Aggregate MNB-HR exists (UI + durable import)",
            )
            _dwell(page, 1500)
            try:
                _ensure_agg_task_and_run()
            except Exception as exc:
                show_banner(page, STEPS[8]["step"], f"Console run note: {exc}")
                _dwell(page, 2000)

            show_banner(page, STEPS[9]["step"], STEPS[9]["callout"])
            _mark(timeline, STEPS[9], t0)
            page.goto(f"{IIQ_BASE}/monitor/tasks/viewTasks.jsf?resetTab=true", wait_until="domcontentloaded")
            _dwell(page, 3000)
            if page.locator("text=Aggregate MNB-HR").count():
                try:
                    page.locator("text=Aggregate MNB-HR").first.click(timeout=5_000)
                    _dwell(page, 2500)
                except Exception:
                    pass
            show_banner(page, STEPS[9]["step"], "Aggregation started — cubes materializing")
            # Give aggregation time while showing the tasks UI
            for _ in range(12):
                _dwell(page, 5000)

            # --- Identities ---
            show_banner(page, STEPS[10]["step"], STEPS[10]["callout"])
            _mark(timeline, STEPS[10], t0)
            page.goto(f"{IIQ_BASE}/define/identity/identities.jsf", wait_until="domcontentloaded")
            _dwell(page, 2500)
            search = page.locator(
                'input[type="text"][name*="search"], input[id*="search"], '
                'input[placeholder*="Search" i], input[name*="filter"]'
            ).first
            try:
                if search.count():
                    point_at(page, search)
                    search.fill("Helen")
                    search.press("Enter")
                    _dwell(page, 3000)
            except Exception:
                pass
            try:
                if page.locator("text=Helen Ross").count():
                    page.locator("text=Helen Ross").first.click(timeout=5_000)
                    _dwell(page, 2500)
                if page.locator("text=Accounts").count():
                    page.locator("text=Accounts").first.click(timeout=5_000)
                    _dwell(page, 2500)
            except Exception:
                pass
            show_banner(page, STEPS[10]["step"], "Confirm MNB-HR account on the cube")
            _dwell(page, 3000)

            # --- End card ---
            show_title_card(
                page,
                "Lesson 04 complete",
                "Next: Lesson 06 — Refresh MNB Attributes / Managers",
            )
            _mark(timeline, STEPS[11], t0)
            _dwell(page, 5000)
            clear_overlays(page)

        except Exception as e:
            try:
                page.screenshot(path=str(fail_shot), full_page=True)
            except Exception:
                pass
            raise SystemExit(f"Recording failed: {e}\nScreenshot: {fail_shot}") from e
        finally:
            context.close()
            browser.close()

    # Attach audio
    segments = synthesize_segments(STEPS, audio_dir)
    # Merge videoStartMs from timeline into segments
    by_id = {t["id"]: t for t in timeline}
    for seg in segments:
        if seg["id"] in by_id:
            seg["videoStartMs"] = by_id[seg["id"]].get("videoStartMs")

    report = {
        "lesson": "04",
        "stem": "04-authoritative-hr-source",
        "baseUrl": IIQ_BASE,
        "hrFile": HR_FILE_DOCKER,
        "timeline": timeline,
        "segments": segments,
        "videoDir": str(video_dir),
        "audioDir": str(audio_dir),
    }
    write_timeline(out_dir / "timeline.json", report)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Record Lesson 04 IIQ lab tutorial")
    ap.add_argument("--out", type=Path, default=OUT / "04")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--slow-mo", type=int, default=0)
    args = ap.parse_args()
    report = run(args.out, headless=not args.headed, slow_mo=args.slow_mo)
    print(json.dumps({"ok": True, "timeline": str(args.out / "timeline.json"), "steps": len(report["timeline"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
