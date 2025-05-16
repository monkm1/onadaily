import os

from patchright.async_api import Page, Playwright

from config import Site


async def makebrowser(playwright: Playwright, headless: bool = False):
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


async def check_logined(page: Page, site: Site) -> bool:
    element = page.locator(site.login_check_xpath)

    if await element.count() == 0:
        return False
    else:
        return True


async def wait_login(page: Page, site: Site) -> None:
    element = page.locator(site.login_check_xpath)
    await element.wait_for(state="visible")
