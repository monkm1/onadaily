import logging
import os
from typing import Pattern
from urllib.parse import urlparse

from patchright.async_api import BrowserContext, Locator, Page, Playwright

import consts
from config import Site

logger = logging.getLogger("onadaily")


async def makebrowser(playwright: Playwright, headless: bool = False) -> BrowserContext:
    datadir = os.path.abspath("./userdata")

    user_agent = playwright.devices["Desktop Chrome"]["user_agent"]

    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir=datadir,
        headless=headless,
        channel="chrome",
        no_viewport=True,
        user_agent=user_agent,
    )
    return browser


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


async def check_logined(page: Page, site: Site) -> bool:
    element = locator(page, site.login_check_xpath)

    if await element.count() == 0:
        return False
    else:
        return True


async def wait_login(page: Page, site: Site) -> None:
    element = locator(page, site.login_check_xpath)
    await element.wait_for(state="visible")
