import abc
import logging

from patchright.async_api import Dialog, Page

import playwrighthelper
from config import Site
from errors import AlreadyStamped, ParseError, StampFailedError
from utils import HandlePlayWrightError, check_already_stamp

logger = logging.getLogger("onadaily")


class BaseStampStrategy(abc.ABC):
    def __init__(self, page: Page) -> None:
        self.working_page = page

    async def stamp(self, site: Site) -> None:
        await self._prepare_stamp(site)
        calendar_page = await self._get_calendar_source(site)

        try:
            if check_already_stamp(site.name, calendar_page):
                raise AlreadyStamped(f"{site.name} : 이미 출첵함")
        except ParseError as ex:
            raise StampFailedError("달력 파싱 중 오류 발생") from ex

        async with self.working_page.expect_event("dialog") as dialog_info:
            await self._click_stamp_button(site)
        dialog = await dialog_info.value
        await self._process_dialog(dialog)

    @HandlePlayWrightError(StampFailedError, "출석 체크 준비 중 실패")
    async def _prepare_stamp(self, site: Site) -> None:
        logger.debug(f"{site.name} 출첵 페이지로 이동: {site.stamp_url}")
        await self.working_page.goto(site.stamp_url)

    @HandlePlayWrightError(StampFailedError, "달력 가져오기 실패")
    async def _get_calendar_source(self, site: Site) -> str:
        calender = playwrighthelper.locator(self.working_page, site.stamp_calendar)
        return await calender.inner_html()

    @HandlePlayWrightError(StampFailedError, "출석 체크 버튼 클릭 실패")
    async def _click_stamp_button(self, site: Site):
        btn_stamp = playwrighthelper.locator(self.working_page, site.btn_stamp)
        await btn_stamp.click()

    @HandlePlayWrightError(StampFailedError, "다이얼로그 처리 중 실패")
    async def _process_dialog(self, dialog: Dialog) -> None:
        # 다이얼로그 처리는 별도 핸들러에서 진행하므로 여기서 accept 금지
        logger.info(f"메시지: {dialog.message}")


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


def get_stamp_strategy(page: Page, site: Site) -> BaseStampStrategy:
    if site.name == "banana":
        return BananaStampStrategy(page)
    else:
        return DefaultStampStrategy(page)
