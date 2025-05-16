import abc
import logging
from typing import Iterable

from bs4 import BeautifulSoup, Tag
from patchright.async_api import Dialog, Page

import playwrighthelper
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
from utils import HandlePlayWrightError, check_already_stamp

logger = logging.getLogger("onadaily")


class BaseLoginStrategy(abc.ABC):  # TODO: 타임아웃 기능 추가
    def __init__(self, page: Page) -> None:
        self.working_page = page

    async def login(self, site: Site) -> None:
        logger.debug(f"{site.name} 로그인 시작 URL : {site.login_url}")
        logger.debug(f"{site.name} 로그인 방식 : {site.login}")

        await self._get_login_url(site)
        if await playwrighthelper.check_logined(self.working_page, site):
            logger.debug(f"{site.name} 로그인 이미 되어있음")
            return

        await self._prepare_login(site)
        await self._type_id_password(site)
        await self._click_login_button(site)
        await self._after_click_login_btn(site)
        await self._wait_login(site)
        await self._final_login(site)

    @HandlePlayWrightError(LoginFailedError, "로그인 URL 열기 실패")
    async def _get_login_url(self, site: Site) -> None:
        await self.working_page.goto(site.login_url)

    @HandlePlayWrightError(LoginFailedError, "로그인 준비 중 실패")
    async def _prepare_login(self, site: Site) -> None:
        pass

    @HandlePlayWrightError(LoginFailedError, "로그인 ID/PWD 입력 실패")
    async def _type_id_password(self, site: Site) -> None:
        if site.login == "default":
            idform = self.working_page.locator(site.input_id)

            if (id := site.id) is None:
                raise ValueError("ID가 None입니다.")
            await idform.fill(id)

            pwdform = self.working_page.locator(site.input_pwd)

            if (password := site.password) is None:
                raise ValueError("Password가 None입니다.")

            await pwdform.fill(password)
            # write id and password
            logger.debug("id/password 입력 완료")

        else:
            logger.debug("default가 아닌 로그인 방식이라 id/password 입력 안함")

    @HandlePlayWrightError(LoginFailedError, "로그인 버튼 클릭 실패")
    async def _click_login_button(self, site: Site) -> None:
        if site.btn_login is None:
            raise LoginFailedError(f"로그인 버튼 클릭 실패/{site.name}에서 지원하지 않는 로그인 방식입니다.")
        async with self.working_page.expect_navigation(url=site.main_url):
            await self.working_page.locator(site.btn_login).click()

    @HandlePlayWrightError(LoginFailedError, "로그인 버튼 클릭 후 처리 실패")
    async def _after_click_login_btn(self, site: Site) -> None:
        pass

    @HandlePlayWrightError(LoginFailedError, "로그인 대기 중 실패")
    async def _wait_login(self, site: Site) -> None:
        await playwrighthelper.wait_login(self.working_page, site)

    @HandlePlayWrightError(LoginFailedError, "로그인 완료 후 처리 실패")
    async def _final_login(self, site: Site) -> None:
        pass


class DefaultLoginStrategy(BaseLoginStrategy):
    pass


class ShowDangLoginStrategy(BaseLoginStrategy):
    @HandlePlayWrightError(LoginFailedError, "로그인 버튼 클릭 실패")
    async def _click_login_button(self, site: Site) -> None:
        if site.btn_login is None:
            raise LoginFailedError(f"{site.name}에서 지원하지 않는 로그인 방식입니다.")

        if site.login == "google":
            async with self.working_page.expect_popup() as popup_info:
                await self.working_page.locator(site.btn_login).click()

            popup = await popup_info.value
            logger.debug(f"로그인 창 : {popup.url}")

            user1 = popup.locator(SHOWDANG_GOOGLE_SELECT_USER_1)

            async with popup.expect_navigation():
                await user1.click()

            login_continue = popup.locator(SHOWDANG_GOOGLE_LOGIN_CONTINUE)

            async with self.working_page.expect_navigation():
                await login_continue.click()
        else:
            await super()._click_login_button(site)


class BananaLoginStrategy(BaseLoginStrategy):
    tmp_page: Page

    @HandlePlayWrightError(LoginFailedError, "로그인 준비 중 실패")
    async def _prepare_login(self, site: Site) -> None:
        await super()._prepare_login(site)

        async with self.working_page.expect_popup() as popup_info:
            login_btn = self.working_page.locator(BNA_LOGIN_WND_XPATH)
            await login_btn.click()

        self.tmp_page = self.working_page
        self.working_page = await popup_info.value
        logger.debug(f"로그인 창 : {self.working_page.url}")

    @HandlePlayWrightError(LoginFailedError, "로그인 버튼 클릭 후 처리 실패")
    async def _after_click_login_btn(self, site):
        self.working_page = self.tmp_page


def get_login_strategy(page: Page, site: Site) -> BaseLoginStrategy:
    match site.name:
        case "showdang":
            return ShowDangLoginStrategy(page)
        case "banana":
            return BananaLoginStrategy(page)
        case _:
            return DefaultLoginStrategy(page)


class BaseStampStrategy(abc.ABC):
    def __init__(self, page: Page) -> None:
        self.working_page = page

    async def stamp(self, site: Site):
        await self._prepare_stamp(site)
        calendar_page = await self._get_calendar_source(site)

        try:
            if check_already_stamp(site, calendar_page):
                raise AlreadyStamped(f"{site.name} : 이미 출첵함")
        except ParseError as ex:
            raise StampFailedError("달력 파싱 중 오류 발생") from ex

        async with self.working_page.expect_event("dialog") as dialog_info:
            await self._click_stamp_button(site)
        dialog = await dialog_info.value
        await self._process_dialog(dialog)

    @HandlePlayWrightError(StampFailedError, "출석 체크 준비 중 실패")
    async def _prepare_stamp(self, site: Site) -> None:
        await self.working_page.goto(site.stamp_url)

    @HandlePlayWrightError(StampFailedError, "달력 가져오기 실패")
    async def _get_calendar_source(self, site: Site) -> str:
        calender = self.working_page.locator(site.stamp_calendar)
        return await calender.inner_html()

    @HandlePlayWrightError(StampFailedError, "출석 체크 버튼 클릭 실패")
    async def _click_stamp_button(self, site: Site):
        btn_stamp = self.working_page.locator(site.btn_stamp)
        await btn_stamp.click()

    @HandlePlayWrightError(StampFailedError, "다이얼로그 처리 중 실패")
    async def _process_dialog(self, dialog: Dialog) -> None:
        logger.info(f"메시지: {dialog.message}")
        await dialog.accept()


class DefaultStampStrategy(BaseStampStrategy):
    pass


class BananaStampStrategy(BaseStampStrategy):
    @HandlePlayWrightError(StampFailedError, "다이얼로그 처리 중 실패")
    async def _process_dialog(self, dialog: Dialog):
        dialog_text = dialog.message
        logger.debug(f"메시지: {dialog_text}")
        if dialog_text == "잠시후 다시 시도해 주세요.":
            raise StampFailedError("바나나 얼럿 처리 실패/알 수 없는 이유")
        elif dialog_text == "이미 출석체크를 하셨습니다.":
            raise StampFailedError("바나나 얼럿 처리 실패/달력 파싱 오류")

        await dialog.accept()


def get_stamp_strategy(page: Page, site: Site) -> BaseStampStrategy:
    if site.name == "banana":
        return BananaStampStrategy(page)
    else:
        return DefaultStampStrategy(page)


class BaseHotDealStrategy(abc.ABC):
    def get_hotdeal_info(self, page_source: str, site: Site) -> SaleTable:
        soup = self._get_soup(page_source)

        table = self._get_hotdeal_table(soup, site)

        products = self._get_product_list(table)

        hotdeallist = self._foreach_products(products)

        resulttable = SaleTable(site)
        resulttable.add_products(hotdeallist)
        return resulttable

    def _get_soup(self, page_source: str) -> BeautifulSoup:
        return BeautifulSoup(page_source, "html.parser")

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
