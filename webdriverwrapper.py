from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait

from config import options


class Webdriverwrapper(webdriver.Chrome):
    def __init__(self, chromeoptions):
        super().__init__(options=chromeoptions)
        self.wait = WebDriverWait(self, options.common.waittime)
        self._quited = False

    def wait_for(self, xpath):
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def move_to(self, element):
        action = ActionChains(self)
        action.move_to_element(element).perform()

    def wait_move_click(self, xpath):
        element = self.wait_for(xpath)
        self.move_to(element)
        self.execute_script("arguments[0].click()", element)
        return element

    def find_xpath(self, xpath):
        return self.find_elements(By.XPATH, xpath)

    def wait_for_alert(self):
        self.wait.until(EC.alert_is_present())

    def quit(self):
        if not self._quited:
            super().quit()
            self._quited = True
