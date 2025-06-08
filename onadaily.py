import asyncio
import functools
import logging
from typing import Awaitable

from patchright.async_api import BrowserContext, Dialog, Page, async_playwright
from prettytable import PrettyTable

from classes import StampResult, WorkingAnimation
from config import Options, Site
from consts import ALWAYS_SAVE_LOG
from errors import AlreadyStamped, HotDealDataNotFoundError, LoginFailedError, StampFailedError
from hotdealstrategies import get_hotdeal_strategy
from loginstrategies import get_login_strategy
from logsupport import LogCaptureContext, LoggingInfo, async_id, save_log
from playwrighthelper import make_browser, normalize_url
from stampstrategies import get_stamp_strategy

logger = logging.getLogger("onadaily")


async def handle_dialog(dialog: Dialog, capture_id: str | None) -> None:
    if capture_id is None:
        logger.warning("컨텍스트 id 설정되지 않음")
        await dialog.accept()
        return

    token = async_id.set(capture_id)

    try:
        logger.debug(f"다이얼로그 발생 : {dialog.message}")
        await dialog.accept()
    finally:
        async_id.reset(token)


class Onadaily(object):  # TODO: 버전 정보 추가
    def __init__(self) -> None:
        self.passed: dict[Site, StampResult] = {}
        self.options = Options()

        for site in self.options.common.order:
            self.passed[site] = StampResult(site)
        self.keywordnoti = PrettyTable()
        self.keywordnoti.field_names = ["사이트", "품명", "정상가", "할인가"]

        self.latest_logginginfo: dict[Site, LoggingInfo] = {}

    async def showhotdeal(self, page: Page, site: Site) -> None:
        if self.options.common.showhotdeal and site.hotdeal_table is not None:  # 핫딜 테이블 불러오기
            try:
                hotdeal_strategy = get_hotdeal_strategy(site)
                if normalize_url(page.url) != normalize_url(site.main_url):
                    logger.debug(f"{site.name} 핫딜 파싱을 위해 메인 페이지로 이동: {site.main_url}")
                    await page.goto(site.main_url)
                table = hotdeal_strategy.get_hotdeal_info(await page.content(), site)
            except HotDealDataNotFoundError as e:
                logger.debug(f"핫딜 테이블 파싱 실패 : {e}")
                logger.info("핫딜 테이블을 찾지 못했습니다.")
                return

            if len(table) > 0:
                logger.info(str(table))

                if len(self.options.common.keywordnoti) > 0:  # 키워드 알람 설정됨
                    keywordproducts = table.keywordcheck(self.options.common.keywordnoti)
                    if len(keywordproducts) > 0:
                        self.keywordnoti.add_rows(keywordproducts, divider=True)

    async def check(self, browser: BrowserContext, site: Site, try_count: int) -> StampResult:
        result = StampResult(site)
        log_capture: LogCaptureContext | None = None
        page: Page | None = None
        try:
            log_capture = LogCaptureContext(logger, site.name)
            with log_capture:
                logger.info(f"== {site.name} ==")

                if not site.enable:
                    result.resultmessage = "스킵"
                    result.passed = True
                    return result

                logger.info(f"{try_count}번째 시도")

                page = await browser.new_page()
                dialog_handler = functools.partial(handle_dialog, capture_id=log_capture.capture_id)
                page.on("dialog", dialog_handler)

                login_strategy = get_login_strategy(page, site)
                await login_strategy.login(site)
                logger.info("로그인 성공")

                await self.showhotdeal(page, site)

                stamp_strategy = get_stamp_strategy(page, site)
                await stamp_strategy.stamp(site)

                result.resultmessage = "✅ 출석 체크 성공"
                result.passed = True

        except AlreadyStamped:
            result.resultmessage = "ℹ️ 이미 출첵함"
            result.passed = True
        except (LoginFailedError, StampFailedError) as e:
            result.resultmessage = str(e)
            result.iserror = True
        except Exception as e:
            result.resultmessage = f"❌ 알 수 없는 오류\n\t-{e}"
            result.iserror = True
        finally:
            result.logginginfo = LoggingInfo(log_capture, **site.asdict())
            if page is not None and not page.is_closed():
                await page.close()

            logger.info(result.resultmessage)
            result.logginginfo.add_message(result.resultmessage)

        return result

    async def _run_concurrently(self, jobs) -> list[StampResult]:
        results = []
        results_with_exceptions: list[StampResult | Exception] = await asyncio.gather(*jobs, return_exceptions=True)
        for exornot in results_with_exceptions:
            if isinstance(exornot, Exception):
                raise exornot
            else:
                results.append(exornot)

        return results

    async def _run_sequentially(self, jobs) -> list[StampResult]:
        results = []

        for job in jobs:
            results.append(await job)

        return results

    async def run(self) -> None:
        retry_count = 0
        max_retries = self.options.common.retrytime if self.options.common.autoretry else 1
        isconcurrent = self.options.common.concurrent
        print(f"최대 재시도 횟수 : {max_retries}")

        while retry_count < max_retries and not all(self.passed.values()):
            retry_count += 1
            order = self.options.common.order
            jobs: list[Awaitable] = []

            browser_loading_anim = WorkingAnimation(
                "브라우저 초기화 중",
                "브라우저 초기화 완료",
                "브라우저 초기화 중 오류 발생",
                isconcurrent,
            )
            browser_loading_anim.show_message()

            async with async_playwright() as p:
                browser = await make_browser(p, headless=self.options.common.headless)
                browser.set_default_timeout(self.options.common.waittime * 1000)

                # await remove_cookie(browser)

                await browser_loading_anim.stop()

                for site in order:
                    if self.passed[site]:
                        continue
                    jobs.append(self.check(browser, site, retry_count))

                async with WorkingAnimation(
                    "출석 체크 진행 중", "출석 체크 작업 완료", "출석 체크 중 오류 발생", isconcurrent
                ):
                    if isconcurrent:
                        results = await self._run_concurrently(jobs)
                    else:
                        results = await self._run_sequentially(jobs)

                if isconcurrent:
                    print(f"========== {retry_count}회차 결과 ==========")
                    for result in results:
                        print(result.logginginfo.printlog)

            for result in results:
                self.passed[result.site] = result

                if result.iserror:
                    self.latest_logginginfo[result.site] = result.logginginfo

                if ALWAYS_SAVE_LOG:
                    save_log(result.logginginfo)

        if all(self.passed.values()):
            if len(self.options.common.keywordnoti) > 0:
                print("======키워드 알림======")
                if len(self.keywordnoti.rows) > 0:
                    print(self.keywordnoti)
                else:
                    print("키워드 알림 없음")
        else:
            print("===============")
            print(f"❌ 재시도 {max_retries}번 실패")
            failedsites = [result.site for result in self.passed.values() if not result.passed]
            print(f"실패한 사이트 : {[str(site) for site in failedsites]}")

            for failedsite in failedsites:
                if failedsite in self.latest_logginginfo:
                    save_log(self.latest_logginginfo[failedsite])

        print("======결과======")
        print(f"시도 횟수: {retry_count}")
        for result in self.passed.values():
            print(f"사이트 : {result.site.name} / {result.resultmessage}")
