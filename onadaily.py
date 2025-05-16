import asyncio
import logging

from patchright.async_api import BrowserContext, Page, async_playwright
from prettytable import PrettyTable

from classes import LogCaptureContext, StampResult
from config import Options, Site
from errors import AlreadyStamped, HotDealDataNotFoundError, LoginFailedError, StampFailedError
from playwrighthelper import makebrowser, remove_cookie
from strategies import get_hotdeal_strategy, get_login_strategy, get_stamp_strategy
from utils import LoggingInfo, save_log_error

logger = logging.getLogger("onadaily")


class Onadaily(object):
    def __init__(self) -> None:
        self.passed: dict[Site, StampResult] = {}
        self.options = Options()

        for site in self.options.sites:
            self.passed[site] = StampResult(site)
        self.keywordnoti = PrettyTable()
        self.keywordnoti.field_names = ["사이트", "품명", "정상가", "할인가"]

        self.last_exceptions: dict[Site, LoggingInfo] = {}

        self.chromeversion = "N/A"

    async def showhotdeal(self, page: Page, site: Site) -> None:
        if self.options.common.showhotdeal and site.hotdeal_table is not None:  # 핫딜 테이블 불러오기
            try:
                hotdeal_strategy = get_hotdeal_strategy(site)
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

    async def check(self, browser: BrowserContext, site: Site) -> tuple[StampResult, LogCaptureContext]:
        result = StampResult(site)
        log_capture: LogCaptureContext
        try:
            async with LogCaptureContext(logger) as capturer:
                logger.info(f"== {site.name} ==")

                if not site.enable:
                    logger.info("skip")
                    result.message = "스킵"
                    result.passed = True
                    return result, capturer

                logger.debug(f"=== {site.name} 출석 체크 시작 ===")
                log_capture = capturer
                page = await browser.new_page()
                login_strategy = get_login_strategy(page, site)
                await login_strategy.login(site)
                logger.info("로그인 성공")

                await self.showhotdeal(page, site)

                stamp_strategy = get_stamp_strategy(page, site)
                await stamp_strategy.stamp(site)

                result.message = "✅ 출석 체크 성공"
                result.passed = True

        except AlreadyStamped:
            result.message = "ℹ️ 이미 출첵함"
            result.passed = True
        except LoginFailedError as e:
            captured_logs = log_capture.captured_logs_string if log_capture is not None else None
            result.message = f"❌ 로그인 중 실패\n\t-{e}"
            result.iserror = True
            self.last_exceptions[site] = LoggingInfo(e, site, self.chromeversion, captured_logs)
        except StampFailedError as e:
            captured_logs = log_capture.captured_logs_string if log_capture is not None else None
            result.message = f"❌ 출석체크 중 실패\n\t-{e}"
            result.iserror = True
            self.last_exceptions[site] = LoggingInfo(e, site, self.chromeversion, captured_logs)
        except Exception as e:
            captured_logs = log_capture.captured_logs_string if log_capture is not None else None
            result.message = f"❌ 알 수 없는 오류\n\t-{e}"
            result.iserror = True
            self.last_exceptions[site] = LoggingInfo(e, site, self.chromeversion, captured_logs)
        finally:
            if result.iserror:
                result.passed = False

        return result, log_capture

    async def run(self) -> None:
        retry_count = 0
        max_retries = self.options.common.retrytime if self.options.common.autoretry else 1

        print(f"최대 재시도 횟수 : {max_retries}")

        while retry_count < max_retries and not all(self.passed.values()):
            retry_count += 1
            order = self.options.common.order

            async with async_playwright() as p:
                browser = await makebrowser(p, headless=self.options.common.headless)
                browser.set_default_timeout(self.options.common.waittime * 1000)
                # await remove_cookie(browser)

                jobs = []

                for site in order:
                    if self.passed[site]:
                        continue
                    jobs.append(self.check(browser, site))

                results: list[tuple[StampResult, LogCaptureContext]] = await asyncio.gather(*jobs)

            print(f"========== {retry_count}회차 결과 ==========")
            for result, log in results:
                self.passed[result.site] = result
                print(log.captured_print_logs_string)

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
                if failedsite in self.last_exceptions:
                    log_file_name = save_log_error(self.last_exceptions[failedsite])

                    print(f"로그 저장됨: {log_file_name}")

        print("======결과======")
        for result in self.passed.values():
            print(f"사이트 : {result.site.name} / {result.message}")
