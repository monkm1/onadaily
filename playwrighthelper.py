import logging
import os
from typing import Pattern
from urllib.parse import urlparse, urlsplit

from patchright.async_api import BrowserContext, Dialog, Locator, Page, Playwright

import consts
from config import Site

logger = logging.getLogger("onadaily")


async def make_browser(playwright: Playwright, headless: bool = False) -> BrowserContext:
    datadir = os.path.abspath("./userdata")

    user_agent = playwright.devices["Desktop Chrome"]["user_agent"]

    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir=datadir,
        headless=headless,
        channel="chrome",
        no_viewport=True,
        user_agent=user_agent,
        args=["--window-size=1280,720"],
    )
    return browser


async def make_page(browser: BrowserContext) -> Page:
    async def handle_dialog(dialog: Dialog) -> None:
        logger.debug(f"다이얼로그 발생 : {dialog.message}")
        await dialog.accept()

    page = await browser.new_page()
    page.on("dialog", handle_dialog)
    return page


def locator(
    page: Page,
    selector: str,
    *args,
    has_text: str | Pattern[str] | None = None,
    has_not_text: str | Pattern[str] | None = None,
    has: Locator | None = None,
    has_not: Locator | None = None,
) -> Locator:
    logger.debug(f"locator : {selector}")
    return page.locator(selector, *args, has_text=has_text, has_not_text=has_not_text, has=has, has_not=has_not)


async def remove_cookie(browser: BrowserContext) -> None:
    for site_name, site_url in consts.URLS.items():
        parsed_url = urlparse(site_url)
        target_domain = parsed_url.netloc
        if target_domain.startswith("www."):
            target_domain = target_domain[4:]  # www. 제거
        target_domain = "." + target_domain

        await browser.clear_cookies(domain=target_domain)


async def check_logined(page: Page, site: Site) -> tuple[bool, Locator]:
    element = locator(page, site.login_check_xpath)
    return await element.count() > 0, element


async def wait_login(page: Page, site: Site) -> None:
    element = locator(page, site.login_check_xpath)
    await element.wait_for(state="visible")


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)

    if parsed.netloc and not parsed.scheme:
        url = f"https:{url}"
    if not parsed.scheme:
        url = f"https://{url}"

    parsed = urlsplit(url)

    netloc = parsed.netloc.split(":", 1)
    hostname = netloc[0].lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    path = parsed.path

    if not path:
        path = "/"
    elif path != "/" and path.endswith("/"):
        path = path[:-1]

    return f"{hostname}{path}"
