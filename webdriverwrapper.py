import logging
import os
from typing import Self
from urllib.parse import urlsplit, urlunsplit

import undetected_chromedriver as uc  # type: ignore[import-untyped]
from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait

from config import Site
from consts import DEBUG_MORE_INFO

logger = logging.getLogger("onadaily.webdriverwrapper")

if DEBUG_MORE_INFO:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


class WebDriverWrapper(uc.Chrome):
    def __init__(self, chromeoptions: uc.ChromeOptions, waittime: int, usedatadir: bool = False) -> None:
        self._quited = True
        if usedatadir:
            datadir = os.path.abspath("./userdata")
            logger.debug(f"datadir: {datadir}")
        else:
            datadir = None

        super().__init__(options=chromeoptions, user_data_dir=datadir, debug=True)
        self.wait = WebDriverWait(self, waittime)
        self._quited = False

    def wait_for(self, xpath: str) -> WebElement:
        logger.debug(f"wait_for: {xpath}")
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def wait_for_selector(self, selector: str) -> WebElement:
        logger.debug(f"wait_for_selector: {selector}")
        return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def wait_login(self, site: Site) -> None:
        chkxpath = site.login_check_xpath
        logger.debug(f"wait_login: {chkxpath}")
        self.wait_for(chkxpath)

    def check_logined(self, site: Site) -> bool:
        chkxpath = site.login_check_xpath
        ele = self.find_xpath(chkxpath)
        if ele:
            return True
        return False

    def remove_query(self) -> str:
        return urlunsplit(urlsplit(self.current_url)._replace(query="", fragment=""))

    def check_login_url(self, site: Site) -> bool:
        if site.name != "banana":
            if self.remove_query() != site.login_url:
                return False
            return True
        else:
            if self.find_elements(By.XPATH, "//div[text() = '회원 로그인']"):
                return True
            return False

    def move_to(self, element: WebElement) -> None:
        action = ActionChains(self)
        action.move_to_element(element).perform()

    def wait_move_click(self, xpath: str) -> WebElement:
        element = self.wait_for(xpath)
        self.move_to(element)
        self.execute_script("arguments[0].click();", element)
        return element

    def find_xpath(self, xpath: str) -> list[WebElement]:
        logger.debug(f"find_xpath: {xpath}")
        return self.find_elements(By.XPATH, xpath)

    def wait_for_alert(self) -> None:
        logger.debug("wait_for_alert")
        self.wait.until(EC.alert_is_present())

    def quit(self) -> None:
        if not self._quited:
            self._quited = True
            super().quit()
            logger.debug("quited")

    def get(self, url: str) -> None:
        logger.debug(f"get: {url}")
        super().get(url)

    @property
    def quited(self) -> bool:
        return self._quited

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.quit()

    def cleartextarea(self, element: WebElement) -> None:
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
