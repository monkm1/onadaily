from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait

from classes import HotdealInfo
from config import Site, options
from saletable import SaleTable


class Webdriverwrapper(webdriver.Chrome):
    def __init__(self, chromeoptions):
        self._quited = True
        super().__init__(options=chromeoptions)
        self.wait = WebDriverWait(self, options.common.waittime)
        self._quited = False

    def wait_for(self, xpath) -> WebElement:
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def wait_for_selector(self, selector) -> WebElement:
        return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def wait_login(self, site):
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

    def check_login_url(self, site) -> bool:
        if site.name != "banana":
            if self.remove_query() != site.login_url:
                return False
            return True
        else:
            if self.find_elements(By.XPATH, "//div[text() = '회원 로그인']"):
                return True
            return False

    def move_to(self, element) -> None:
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

    def gethotdealinfo(self, site: Site) -> SaleTable:
        soup = BeautifulSoup(self.page_source, "html.parser")
        soup = soup.select_one(site.hotdeal_table).select_one("div")  # type: ignore
        products_all = soup.find_all("div", recursive=False)
        products = []
        for p in products_all:
            if p.has_attr("data-swiper-slide-index") and "swiper-slide-duplicate" not in p["class"]:
                productsoup = list(p.children)[1]

                price = dc_price = name = "이게 보이면 오류"
                if site.name == "onami":
                    dc_price = productsoup.find("p", "price").find("span").text
                    price = productsoup.find("strike").text
                    name = productsoup.find("p", "name").text

                elif site.name == "showdang":
                    price = productsoup.find("span", "or-price").text
                    dc_price = productsoup.find("span", "sl-price").text
                    name = productsoup.find("ul", "swiper-prd-info-name").text

                products.append(HotdealInfo(name, price, dc_price))

        table = SaleTable(site)
        table.field_names = ["품명", "정상가", "할인가"]
        table.add_rows([x.to_row() for x in products])
        return table

    def quit(self) -> None:
        if not self._quited:
            super().quit()
            self._quited = True
