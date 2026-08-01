"""IIQ login helpers for Playwright."""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from . import IIQ_BASE, IIQ_PASSWORD, IIQ_USER


def login(page: Page, user: str | None = None, password: str | None = None) -> None:
    """Log into IdentityIQ (JSF login form)."""
    u = user or IIQ_USER
    p = password or IIQ_PASSWORD
    page.goto(f"{IIQ_BASE}/login.jsf", wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(800)

    # Common IIQ 8.x login field names / placeholders
    user_box = page.locator(
        'input[name="loginForm:accountId"], input#loginForm\\:accountId, '
        'input[name="accountId"], input[placeholder*="User" i], input[type="text"]'
    ).first
    pass_box = page.locator(
        'input[name="loginForm:password"], input#loginForm\\:password, '
        'input[name="password"], input[type="password"]'
    ).first
    user_box.wait_for(state="visible", timeout=30_000)
    user_box.fill(u)
    pass_box.fill(p)

    submit = page.locator(
        'input[type="submit"], button[type="submit"], '
        'input[name="loginForm:loginButton"], button:has-text("Log In"), '
        'button:has-text("Login"), a:has-text("Login")'
    ).first
    submit.click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)

    # Home / dashboard should not still be login
    if "login.jsf" in page.url:
        pass_box.press("Enter")
        page.wait_for_timeout(2000)
    page.wait_for_url(re.compile(r".*/(home|dashboard|rapidSetupHome).jsf.*"), timeout=30_000)
    expect(page).not_to_have_url(re.compile(r".*login\.jsf.*"), timeout=5_000)
