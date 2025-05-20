import abc
import logging

from patchright.async_api import Locator, Page

import playwrighthelper
from config import Site
from consts import BNA_LOGIN_WND_XPATH, SHOWDANG_GOOGLE_LOGIN_CONTINUE, SHOWDANG_GOOGLE_SELECT_USER_1
from errors import LoginFailedError
from utils import HandlePlayWrightError

logger = logging.getLogger("onadaily")


class BaseLoginStrategy(abc.ABC):
    def __init__(self, page: Page) -> None:
        self.working_page = page

    async def login(self, site: Site) -> None:
        logger.debug(f"{site.name} 로그인 시작 URL : {site.login_url}")
        logger.debug(f"{site.name} 로그인 방식 : {site.login}")

        await self._goto_main_url(site)
        await self.working_page.reload()  # 가짜 로그인(실제로는 로그인 상태 아님) 방지용
        islogined, logoutbtn = await playwrighthelper.check_logined(self.working_page, site)
        if islogined:
            logger.debug(f"{site.name} 로그인 이미 되어있음")
            # await self._logout(site, logoutbtn)
            return
        await self._goto_login_url(site)

        await self._prepare_login(site)
        await self._type_id_password(site)
        await self._click_login_button(site)
        await self._after_click_login_btn(site)
        await self._wait_login(site)
        await self._final_login(site)

    @HandlePlayWrightError(LoginFailedError, "로그아웃 중 실패")
    async def _logout(self, site: Site, logoutbtn: Locator) -> None:
        async with self.working_page.expect_navigation(url=site.main_url):
            await logoutbtn.click()

    @HandlePlayWrightError(LoginFailedError, "메인 페이지 URL 열기 실패")
    async def _goto_main_url(self, site: Site) -> None:
        logger.debug(f"{site.name} 메인 페이지로 이동: {site.main_url}")
        await self.working_page.goto(site.main_url)

    @HandlePlayWrightError(LoginFailedError, "로그인 URL 열기 실패")
    async def _goto_login_url(self, site: Site) -> None:
        logger.debug(f"{site.name} 로그인 페이지로 이동: {site.login_url}")
        await self.working_page.goto(site.login_url)

    @HandlePlayWrightError(LoginFailedError, "로그인 준비 중 실패")
    async def _prepare_login(self, site: Site) -> None:
        pass

    @HandlePlayWrightError(LoginFailedError, "로그인 ID/PWD 입력 실패")
    async def _type_id_password(self, site: Site) -> None:
        if site.login == "default":
            idform = playwrighthelper.locator(self.working_page, site.input_id)

            if (id := site.id) is None:
                raise ValueError("ID가 None입니다.")
            await idform.fill(id)

            pwdform = playwrighthelper.locator(self.working_page, site.input_pwd)

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
            await playwrighthelper.locator(self.working_page, site.btn_login).click()

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
                await playwrighthelper.locator(self.working_page, site.btn_login).click()

            popup = await popup_info.value
            logger.debug(f"로그인 창 : {popup.url}")

            user1 = playwrighthelper.locator(popup, SHOWDANG_GOOGLE_SELECT_USER_1)

            async with popup.expect_navigation():
                await user1.click()

            login_continue = playwrighthelper.locator(popup, SHOWDANG_GOOGLE_LOGIN_CONTINUE)

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
            login_btn = playwrighthelper.locator(self.working_page, BNA_LOGIN_WND_XPATH)
            await login_btn.click()

        self.tmp_page = self.working_page
        self.working_page = await popup_info.value
        logger.debug(f"로그인 창 : {self.working_page.url}")

    @HandlePlayWrightError(LoginFailedError, "로그인 버튼 클릭 후 처리 실패")
    async def _after_click_login_btn(self, site):
        self.working_page = self.tmp_page


class DingdongLoginStrategy(BaseLoginStrategy):
    @HandlePlayWrightError(LoginFailedError, "로그아웃 중 실패")
    async def _logout(self, site: Site, logoutbtn: Locator) -> None:
        await logoutbtn.click()
        await self.working_page.goto(site.main_url)


def get_login_strategy(page: Page, site: Site) -> BaseLoginStrategy:
    match site.name:
        case "showdang":
            return ShowDangLoginStrategy(page)
        case "banana":
            return BananaLoginStrategy(page)
        case "dingdong":
            return DingdongLoginStrategy(page)
        case _:
            return DefaultLoginStrategy(page)
