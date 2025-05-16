import os
from urllib.parse import urlparse

from patchright.async_api import BrowserContext, Page, Playwright

import consts
from config import Site


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


async def remove_cookie(browser: BrowserContext) -> None:
    all_cookies = await browser.cookies()
    for site_name, site_url in consts.URLS.items():
        parsed_url = urlparse(site_url)
        target_domain = parsed_url.netloc
        if target_domain.startswith("www."):
            target_domain = target_domain[4:]  # www. 제거
        target_domain = "." + target_domain

        await browser.clear_cookies(domain=target_domain)


async def check_logined(page: Page, site: Site) -> bool:
    element = page.locator(site.login_check_xpath)

    if await element.count() == 0:
        return False
    else:
        return True


async def wait_login(page: Page, site: Site) -> None:
    element = page.locator(site.login_check_xpath)
    await element.wait_for(state="visible")
