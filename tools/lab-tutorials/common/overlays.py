"""On-screen callout / pointer overlays injected into the page."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

OVERLAY_CSS = """
#mnb-tut-banner {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 2147483646;
  background: linear-gradient(90deg, #0b1f33 0%, #123a5c 100%);
  color: #f4f7fb; font: 600 16px/1.35 "DM Sans", system-ui, sans-serif;
  padding: 14px 20px 16px; box-shadow: 0 -6px 24px rgba(0,0,0,.35);
  pointer-events: none;
}
#mnb-tut-banner .mnb-step {
  display: inline-block; font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
  opacity: .75; margin-bottom: 4px;
}
#mnb-tut-banner .mnb-text { display: block; max-width: 1100px; }
#mnb-tut-titlecard {
  position: fixed; inset: 0; z-index: 2147483647;
  display: flex; align-items: center; justify-content: center;
  background: radial-gradient(ellipse at 30% 20%, #1a4a73 0%, #071422 55%, #040a12 100%);
  color: #f4f7fb; text-align: center; pointer-events: none;
  font-family: "Fraunces", Georgia, serif;
}
#mnb-tut-titlecard h1 { font-size: 42px; margin: 0 0 12px; font-weight: 700; }
#mnb-tut-titlecard p { font: 500 18px/1.5 "DM Sans", system-ui, sans-serif; opacity: .9; max-width: 640px; margin: 0 auto; }
#mnb-tut-pointer {
  position: fixed; z-index: 2147483646; width: 28px; height: 28px;
  border: 3px solid #ffb020; border-radius: 50%;
  box-shadow: 0 0 0 6px rgba(255,176,32,.25), 0 0 18px rgba(255,176,32,.55);
  pointer-events: none; transform: translate(-50%, -50%);
  transition: left .35s ease, top .35s ease;
}
#mnb-tut-pointer::after {
  content: ""; position: absolute; left: 50%; top: 100%;
  width: 2px; height: 36px; background: #ffb020; transform: translateX(-50%);
}
"""


def ensure_overlay_root(page: Page) -> None:
    page.evaluate(
        """(css) => {
          if (!document.getElementById('mnb-tut-style')) {
            const s = document.createElement('style');
            s.id = 'mnb-tut-style';
            s.textContent = css;
            document.documentElement.appendChild(s);
          }
        }""",
        OVERLAY_CSS,
    )


def show_title_card(page: Page, title: str, subtitle: str) -> None:
    ensure_overlay_root(page)
    page.evaluate(
        """({title, subtitle}) => {
          let el = document.getElementById('mnb-tut-titlecard');
          if (!el) {
            el = document.createElement('div');
            el.id = 'mnb-tut-titlecard';
            document.documentElement.appendChild(el);
          }
          el.innerHTML = `<div><h1></h1><p></p></div>`;
          el.querySelector('h1').textContent = title;
          el.querySelector('p').textContent = subtitle;
          el.style.display = 'flex';
        }""",
        {"title": title, "subtitle": subtitle},
    )


def hide_title_card(page: Page) -> None:
    page.evaluate(
        """() => {
          const el = document.getElementById('mnb-tut-titlecard');
          if (el) el.style.display = 'none';
        }"""
    )


def show_banner(page: Page, step: str, text: str) -> None:
    ensure_overlay_root(page)
    page.evaluate(
        """({step, text}) => {
          let el = document.getElementById('mnb-tut-banner');
          if (!el) {
            el = document.createElement('div');
            el.id = 'mnb-tut-banner';
            document.documentElement.appendChild(el);
          }
          el.innerHTML = `<span class="mnb-step"></span><span class="mnb-text"></span>`;
          el.querySelector('.mnb-step').textContent = step;
          el.querySelector('.mnb-text').textContent = text;
          el.style.display = 'block';
        }""",
        {"step": step, "text": text},
    )


def hide_banner(page: Page) -> None:
    page.evaluate(
        """() => {
          const el = document.getElementById('mnb-tut-banner');
          if (el) el.style.display = 'none';
        }"""
    )


def point_at(page: Page, locator: Locator | None) -> None:
    ensure_overlay_root(page)
    if locator is None:
        page.evaluate(
            """() => {
              const el = document.getElementById('mnb-tut-pointer');
              if (el) el.remove();
            }"""
        )
        return
    box = locator.bounding_box()
    if not box:
        return
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2
    page.evaluate(
        """({x, y}) => {
          let el = document.getElementById('mnb-tut-pointer');
          if (!el) {
            el = document.createElement('div');
            el.id = 'mnb-tut-pointer';
            document.documentElement.appendChild(el);
          }
          el.style.left = x + 'px';
          el.style.top = y + 'px';
        }""",
        {"x": x, "y": y},
    )


def clear_overlays(page: Page) -> None:
    hide_title_card(page)
    hide_banner(page)
    point_at(page, None)
