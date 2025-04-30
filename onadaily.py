import logging

from prettytable import PrettyTable

from classes import StampResult
from config import Options, Site
from errors import AlreadyStamped, HotDealDataNotFoundError, LoginFailedError, StampFailedError
from strategies import get_hotdeal_strategy, get_login_strategy, get_stamp_strategy
from utils import LoggingInfo, get_chrome_options, save_log_error
from webdriverwrapper import WebDriverWrapper

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

    def initdriver(self) -> WebDriverWrapper:
        driver = WebDriverWrapper(
            get_chrome_options(self.options.common.headless),
            self.options.common.waittime,
        )

        return driver

    def showhotdeal(self, driver: WebDriverWrapper, site: Site) -> None:
        if self.options.common.showhotdeal and site.hotdeal_table is not None:  # 핫딜 테이블 불러오기
            try:
                hotdeal_strategy = get_hotdeal_strategy(site)
                table = hotdeal_strategy.get_hotdeal_info(driver, site)
            except HotDealDataNotFoundError as e:
                logger.debug(f"핫딜 테이블 파싱 실패 : {e}")
                print("핫딜 테이블을 찾지 못했습니다.")
                return

            if len(table) > 0:
                print(table)

                if len(self.options.common.keywordnoti) > 0:  # 키워드 알람 설정됨
                    keywordproducts = table.keywordcheck(self.options.common.keywordnoti)
                    if len(keywordproducts) > 0:
                        self.keywordnoti.add_rows(keywordproducts)

    def check(self, driver: WebDriverWrapper, site: Site) -> StampResult:
        result = StampResult(site)
        try:
            print(f"== {site.name} ==")

            if not site.enable:
                print("skip")
                result.message = "스킵"
                result.passed = True
                return result

            login_strategy = get_login_strategy(site)
            login_strategy.login(driver, site)
            print("로그인 성공")

            self.showhotdeal(driver, site)

            stamp_strategy = get_stamp_strategy(site)
            stamp_strategy.stamp(driver, site)

            result.message = "✅ 출석 체크 성공"
            result.passed = True
        except AlreadyStamped:
            result.message = "ℹ️ 이미 출첵함"
            result.passed = True
        except LoginFailedError as e:
            result.message = f"❌ 로그인 중 실패\n\t-{e}"
            result.iserror = True
            self.last_exceptions[site] = LoggingInfo(e, site, driver)
        except StampFailedError as e:
            result.message = f"❌ 출석체크 중 실패\n\t-{e}"
            result.iserror = True
            self.last_exceptions[site] = LoggingInfo(e, site, driver)
        except Exception as e:
            result.message = f"❌ 알 수 없는 오류\n\t-{e}"
            result.iserror = True
            self.last_exceptions[site] = LoggingInfo(e, site, driver)
        finally:
            if result.iserror:
                result.passed = False

        print(result.message)
        return result

    def run(self) -> None:
        retry_count = 0
        max_retries = self.options.common.retrytime if self.options.common.autoretry else 1

        while retry_count < max_retries and not all(self.passed.values()):
            retry_count += 1
            order = self.options.common.order

            with self.initdriver() as driver:
                for site in order:
                    self._currentsite = site
                    if self.passed[site]:
                        continue

                    self.passed[site] = self.check(driver, site)

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
                    save_log_error(self.last_exceptions[failedsite])

        print("======결과======")
        for result in self.passed.values():
            print(f"사이트 : {result.site.name} / {result.message}")
