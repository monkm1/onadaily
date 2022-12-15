from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import getoption


class Webdriverwrapper(webdriver.Chrome):
    def __init__(self, options):
        service = ChromeService(ChromeDriverManager().install())
        super().__init__(service=service, options=options)
        self.wait = WebDriverWait(self, getoption("common", "waittime"))

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
