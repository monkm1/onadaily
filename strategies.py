import abc
import logging
import random
from time import sleep
from typing import Iterable

from bs4 import BeautifulSoup, Tag
from selenium.webdriver.common.alert import Alert

from classes import HotdealInfo, SaleTable
from config import Site
from consts import BNA_LOGIN_WND_XPATH, SHOWDANG_GOOGLE_LOGIN_CONTINUE, SHOWDANG_GOOGLE_SELECT_USER_1
from errors import (
    AlreadyStamped,
    HotDealDataNotFoundError,
    HotDealTableParseError,
    LoginFailedError,
    ParseError,
    StampFailedError,
)
from utils import check_already_stamp, handle_selenium_error
from webdriverwrapper import WebDriverWrapper

logger = logging.getLogger("onadaily")


class BaseLoginStrategy(abc.ABC):
    def __init__(self) -> None:
        self.main_window_handle = ""

    def login(self, driver: WebDriverWrapper, site: Site) -> None:
        logger.debug(f"{site.name} 로그인 시작 URL : {site.login_url}")
        logger.debug(f"{site.name} 로그인 방식 : {site.login}")

        self._get_login_url(driver, site)

        if driver.check_logined(site):
            logger.debug(f"{site.name} 로그인 이미 되어있음")
            return

        self._prepare_login(driver, site)
        self._enter_id_password(driver, site)
        self._click_login_button(driver, site)
        self._final_login(driver, site)
        self._wait_login(driver, site)

    @handle_selenium_error(LoginFailedError, "로그인 url 열기 실패")
    def _get_login_url(self, driver: WebDriverWrapper, site: Site) -> None:
        driver.get(site.login_url)

    @handle_selenium_error(LoginFailedError, "로그인 준비 중 실패")
    def _prepare_login(self, driver: WebDriverWrapper, site: Site) -> None:
        self.main_window_handle = driver.current_window_handle
        logger.debug(f"현재 window 핸들 : {self.main_window_handle}")

    @handle_selenium_error(LoginFailedError, "ID/Password 입력 실패")
    def _enter_id_password(self, driver: WebDriverWrapper, site: Site) -> None:
        if site.login == "default":
            idform = driver.wait_move_click(site.input_id)
            driver.cleartextarea(idform)

            if (id := site.id) is None:
                raise ValueError("ID가 None입니다.")
            idform.send_keys(id)

            pwdform = driver.wait_move_click(site.input_pwd)
            driver.cleartextarea(pwdform)

            if (password := site.password) is None:
                raise ValueError("Password가 None입니다.")

            pwdform.send_keys(password)
            # write id and password
            logger.debug("id/password 입력 완료")

        else:
            logger.debug("default가 아닌 로그인 방식이라 id/password 입력 안함")

    @handle_selenium_error(LoginFailedError, "로그인 버튼 클릭 실패")
    def _click_login_button(self, driver: WebDriverWrapper, site: Site) -> None:
        if site.btn_login is None:
            raise LoginFailedError(f"로그인 버튼 클릭 실패/{site.name}에서 지원하지 않는 로그인 방식입니다.")
        driver.wait_move_click(site.btn_login)

    @handle_selenium_error(LoginFailedError, "로그인 후 처리 실패")
    def _final_login(self, driver: WebDriverWrapper, site: Site) -> None:
        pass

    @handle_selenium_error(LoginFailedError, "로그인 확인 실패")
    def _wait_login(self, driver: WebDriverWrapper, site: Site) -> None:
        logger.debug(f"{site.name} 로그인 확인")
        driver.wait_login(site)


class DefaultLoginStrategy(BaseLoginStrategy):
    pass


class ShowDangLoginStrategy(BaseLoginStrategy):

    @handle_selenium_error(LoginFailedError, "로그인 확인 실패")
    def _final_login(self, driver: WebDriverWrapper, site: Site) -> None:
        super()._final_login(driver, site)
        if site.login == "google":
            another_window = list(set(driver.window_handles) - {self.main_window_handle})[0]
            logger.debug(f"로그인 창 핸들 : {another_window}")
            driver.switch_to.window(another_window)

            driver.wait_move_click(SHOWDANG_GOOGLE_SELECT_USER_1)

            driver.wait_move_click(SHOWDANG_GOOGLE_LOGIN_CONTINUE)

            driver.switch_to.window(self.main_window_handle)


class BananaLoginStrategy(BaseLoginStrategy):

    @handle_selenium_error(LoginFailedError, "로그인 준비 중 실패")
    def _prepare_login(self, driver: WebDriverWrapper, site: Site) -> None:
        super()._prepare_login(driver, site)

        driver.wait_move_click(BNA_LOGIN_WND_XPATH)

        another_window = list(set(driver.window_handles) - {driver.current_window_handle})[0]
        logger.debug(f"로그인 창 핸들 : {another_window}")
        driver.switch_to.window(another_window)

    def _final_login(self, driver: WebDriverWrapper, site: Site) -> None:
        super()._final_login(driver, site)
        driver.switch_to.window(self.main_window_handle)


def get_login_strategy(site: Site) -> BaseLoginStrategy:
    match site.name:
        case "showdang":
            return ShowDangLoginStrategy()
        case "banana":
            return BananaLoginStrategy()
        case _:
            return DefaultLoginStrategy()


class BaseStampStrategy(abc.ABC):
    def stamp(self, driver: WebDriverWrapper, site: Site):
        self._prepare_stamp(driver, site)
        calendar_page = self._get_calendar_source(driver, site)

        try:
            if check_already_stamp(site, calendar_page):
                raise AlreadyStamped(f"{site.name} : 이미 출첵함")
        except ParseError as ex:
            raise StampFailedError("달력 파싱 중 오류 발생") from ex

        self._click_stamp_button(driver, site)
        alert = self._get_alert(driver, site)
        self._handle_alert(alert)

    def _prepare_stamp(self, driver: WebDriverWrapper, site: Site) -> None:
        driver.get(site.stamp_url)

    @handle_selenium_error(StampFailedError, "달력 가져오기 실패")
    def _get_calendar_source(self, driver: WebDriverWrapper, site: Site) -> str:
        driver.wait_for_selector(site.stamp_calendar)
        return driver.page_source

    @handle_selenium_error(StampFailedError, "출첵 버튼 클릭 실패")
    def _click_stamp_button(self, driver: WebDriverWrapper, site: Site):
        if site.name == "onami":
            sleep(random.uniform(0.5, 1.0))  # 버튼 클릭 전 대기

        driver.wait_move_click(site.btn_stamp)

    @handle_selenium_error(StampFailedError, "얼럿 찾기 실패")
    def _get_alert(self, driver: WebDriverWrapper, site: Site) -> Alert:
        driver.wait_for_alert()
        alert = driver.switch_to.alert

        print(f"메시지 : {alert.text}")

        return alert

    @handle_selenium_error(StampFailedError, "얼럿 처리 실패")
    def _handle_alert(self, alert: Alert):
        alert.accept()


class DefaultStampStrategy(BaseStampStrategy):
    pass


class BananaStampStrategy(BaseStampStrategy):
    def _handle_alert(self, alert: Alert):
        alert_text = alert.text
        alert.accept()
        if alert_text == "잠시후 다시 시도해 주세요.":
            raise StampFailedError("바나나 얼럿 처리 실패/알 수 없는 이유")
        elif alert_text == "이미 출석체크를 하셨습니다.":
            raise StampFailedError("바나나 얼럿 처리 실패/달력 파싱 오류")


def get_stamp_strategy(site: Site) -> BaseStampStrategy:
    if site.name == "banana":
        return BananaStampStrategy()
    else:
        return DefaultStampStrategy()


class BaseHotDealStrategy(abc.ABC):
    def get_hotdeal_info(self, driver: WebDriverWrapper, site: Site) -> SaleTable:
        soup = self._get_soup(driver)

        table = self._get_hotdeal_table(soup, site)

        products = self._get_product_list(table)

        hotdeallist = self._foreach_products(products)

        resulttable = SaleTable(site)
        resulttable.add_products(hotdeallist)
        return resulttable

    def _get_soup(self, driver: WebDriverWrapper) -> BeautifulSoup:
        return BeautifulSoup(driver.page_source, "html.parser")

    def _get_hotdeal_table(self, soup: BeautifulSoup, site: Site) -> Tag:
        if site.hotdeal_table is None:
            raise HotDealTableParseError("잘못된 사이트 설정")
        table = soup.select_one(site.hotdeal_table)

        if table is None:
            raise HotDealDataNotFoundError("핫딜 테이블 찾을 수 없음")

        return table

    def _get_product_list(self, table: Tag) -> Iterable[Tag]:
        if (div := table.select_one("div")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")

        products = div.find_all("div", recursive=False)

        if len(products) == 0:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")

        result = [
            list(x.children)[1]
            for x in products
            if x.has_attr("data-swiper-slide-index") and "swiper-slide-duplicate" not in x["class"]
        ]
        return result

    def _foreach_products(self, products: Iterable[Tag]) -> list[HotdealInfo]:
        hotdealinfolist = []
        for product in products:
            try:
                info = self._get_product_info(product)
            except HotDealDataNotFoundError:
                logger.debug("핫딜 파싱 중 상품이 없음")
                continue

            hotdealinfolist.append(info)

        return hotdealinfolist

    @abc.abstractmethod
    def _get_product_info(self, product: Tag) -> HotdealInfo:
        pass


class OnamiHotDealStrategy(BaseHotDealStrategy):
    def _get_product_info(self, product: Tag) -> HotdealInfo:
        price = dc_price = name = "이게 보이면 오류"

        if (dcpricespan := product.select_one("p.price > span")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")
        dc_price = dcpricespan.text

        if (pricestrike := product.select_one("strike")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")

        price = pricestrike.text

        if (namep := product.select_one("p.name")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")

        name = namep.text

        return HotdealInfo(name, price, dc_price)


class ShowDangHotDealStrategy(BaseHotDealStrategy):
    def _get_product_info(self, product: Tag) -> HotdealInfo:
        price = dc_price = name = "이게 보이면 오류"

        if (price_span := product.select_one("span.or-price")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")
        price = price_span.text

        if (dc_price_span := product.select_one("span.sl-price")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")
        dc_price = dc_price_span.text

        if (name_ul := product.select_one("ul.swiper-prd-info-name")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")
        name = name_ul.text

        return HotdealInfo(name, price, dc_price)


def get_hotdeal_strategy(site: Site) -> BaseHotDealStrategy:
    if site.name == "onami":
        return OnamiHotDealStrategy()
    elif site.name == "showdang":
        return ShowDangHotDealStrategy()
    else:
        raise HotDealTableParseError(f"{site.name} 핫딜 테이블 파싱 지원 안됨")
