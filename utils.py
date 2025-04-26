import functools
import os
import sys
import traceback
from datetime import datetime
from math import ceil
from os import path
from typing import Any, Callable, Type

import pytz
import undetected_chromedriver as uc  # type: ignore[import-untyped]
from bs4 import BeautifulSoup
from selenium.common import (
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException,
    UnexpectedAlertPresentException,
    WebDriverException,
)

from classes import HotdealInfo
from config import Site
from saletable import SaleTable
from webdriverwrapper import Webdriverwrapper


class ParseError(Exception):
    pass


class LoginFailedError(Exception):
    pass


class StampFailedError(Exception):
    pass


class AlreadyStamped(Exception):
    pass


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
    date = datetime.now(pytz.timezone("Asia/Seoul"))
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
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"  # noqa
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


def gethotdealinfo(page_source: str, site: Site) -> SaleTable | None:
    soup = BeautifulSoup(page_source, "html.parser")

    if site.hotdeal_table is None:
        raise ParseError("잘못된 사이트 핫딜 파싱 시도함")
    table = soup.select_one(site.hotdeal_table)

    if table is None:
        print("핫딜 테이블 찾을 수 없음")
        return None

    div = table.select_one("div")

    if div is None:
        print("핫딜 테이블 찾을 수 없음")
        return None

    products_all = div.find_all("div", recursive=False)
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

    resulttable = SaleTable(site)
    resulttable.field_names = ["품명", "정상가", "할인가"]
    resulttable.add_rows([x.to_row() for x in products])
    return resulttable


if getattr(sys, "frozen", False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = app_path


class LoggingInfo:
    def __init__(self, site: Site, driver: Webdriverwrapper) -> None:
        self.now = datetime.now()
        self.stacktrace = traceback.format_exc()
        self.site = site

        if driver is not None and not driver.quited:
            try:
                self.version = f"Chrome version : {driver.capabilities['browserVersion']}"
            except:  # noqa
                self.version = "Chrome version : N/A"
        else:
            self.version = "Chrome version : N/A"

    def __str__(self) -> str:
        return (
            f"{self.now}\n\n"
            f"{self.stacktrace}\n\n"
            f"sitename : {self.site}\n"
            f"enable : {self.site.enable}\n"
            f"login : {self.site.login}\n"
            f"{self.version}"
        )


def save_log_error(logginginfo: LoggingInfo):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.join(LOG_DIR, f"error_{timestamp}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(logginginfo))

    except Exception as ex:
        print(f"로깅 실패 : {ex}")
        print(f"원본 오류 : \n{logginginfo.stacktrace}")


def handle_selenium_error(wrap_exception: Type[Exception], message_prefix: str):
    def inner(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(self, driver: Webdriverwrapper, site: Site, *args, **kwargs):
            try:
                func(self, driver, site, *args, **kwargs)
            except TimeoutException as ex:
                raise wrap_exception(f"{message_prefix}/시간 초과 발생") from ex
            except NoSuchElementException as ex:
                raise wrap_exception(f"{message_prefix}/요소를 찾을 수 없음") from ex
            except UnexpectedAlertPresentException as ex:
                raise wrap_exception(f"{message_prefix}/처리되지 않은 얼럿 발생") from ex
            except NoAlertPresentException as ex:
                raise wrap_exception(f"{message_prefix}/처리할 얼럿 없음") from ex
            except WebDriverException as ex:
                raise wrap_exception(
                    f"{message_prefix}/알 수 없는 셀레니움 에러\n소셜 로그인을 사용중이라면 열려있는 크롬을 모두 닫고 실행하세요."
                ) from ex

        return wrapper

    return inner
