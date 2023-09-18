from urllib.parse import urlsplit, urlunsplit

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait

from config import Site, options


class Webdriverwrapper(webdriver.Chrome):
    def __init__(self, chromeoptions) -> None:
        self._quited = True
        super().__init__(options=chromeoptions)
        self.wait = WebDriverWait(self, options.common.waittime)
        self._quited = False

    def wait_for(self, xpath) -> WebElement:
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def wait_for_selector(self, selector: str) -> WebElement:
        return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def wait_login(self, site: Site) -> None:
        chkxpath = site.login_check_xpath
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

    def wait_move_click(self, xpath) -> WebElement:
        element = self.wait_for(xpath)
        self.move_to(element)
        self.execute_script("arguments[0].click()", element)
        return element

    def find_xpath(self, xpath) -> list[WebElement]:
        return self.find_elements(By.XPATH, xpath)

    def wait_for_alert(self) -> None:
        self.wait.until(EC.alert_is_present())

    def quit(self) -> None:
        if not self._quited:
            super().quit()
            self._quited = True
