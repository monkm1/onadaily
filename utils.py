from datetime import datetime
from math import ceil
from os import path

import pytz
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from classes import HotdealInfo
from config import Site
from saletable import SaleTable


class ParseError(Exception):
    pass


def cleartextarea(element: WebElement) -> None:
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.DELETE)


def check_already_stamp(site: Site, source: str) -> bool:
    soup = BeautifulSoup(source, "html.parser")
    tablesoup = soup.select_one(site.stamp_calendar)

    if tablesoup is None:
        raise ParseError("오류 : 달력을 찾을 수 없습니다.")

    week, day = num_of_month_week()

    weekssoup = tablesoup.find_all(True, recursive=False)
    weeksoup = weekssoup[week - 1].find_all(True, recursive=False)

    todaysoup = weeksoup[day - 1]

    if site.name != "banana":
        if todaysoup.find("img", {"alt": "출석"}) is None:
            return False
        else:
            return True
    else:
        if todaysoup.find("img") is None:
            return False
        else:
            return True


def num_of_month_week() -> tuple[int, int]:
    utcnow = pytz.utc.localize(datetime.utcnow())
    date = utcnow.astimezone(pytz.timezone("Asia/Seoul"))

    date = datetime.today()
    first_day = date.replace(day=1)

    day_of_month = date.day

    if first_day.weekday() == 6:
        adjusted_dom = day_of_month + 1
    else:
        adjusted_dom = day_of_month + first_day.weekday() + 1

    weeknum = int(ceil(adjusted_dom / 7.0))
    dayofweeknum = (date.weekday() + 1) % 7 + 1

    return weeknum, dayofweeknum


def get_chrome_options(reqdatadir=False, datadir="", profile="", headless=False) -> uc.ChromeOptions:
    chromeoptions = uc.ChromeOptions()
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    chromeoptions.add_argument(f"--user-agent={useragent}")
    chromeoptions.add_argument("--disable-extensions")
    chromeoptions.add_argument("--log-level=3")
    chromeoptions.add_argument("--disable-popup-blocking")

    if headless:
        chromeoptions.add_argument("--disable-gpu")
        chromeoptions.add_argument("--headless")
        chromeoptions.add_argument("--window-size=1920,1080")
        chromeoptions.add_argument("--no-sandbox")
        chromeoptions.add_argument("--start-maximized")
        chromeoptions.add_argument("--disable-setuid-sandbox")
    if reqdatadir:
        datadir = path.expandvars(datadir)
        chromeoptions.add_argument(f"--user-data-dir={datadir}")
        chromeoptions.add_argument(f"--profile-directory={profile}")

    return chromeoptions


def gethotdealinfo(page_source: str, site: Site) -> SaleTable:
    soup = BeautifulSoup(page_source, "html.parser")
    soup = soup.select_one(site.hotdeal_table)

    if soup is None:
        print("핫딜 테이블 찾을 수 없음")
        return None

    soup = soup.select_one("div")
    # type: ignore
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
