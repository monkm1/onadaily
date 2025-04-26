import logging

from prettytable import PrettyTable

from config import Site, options
from strategies import get_login_strategy, get_stamp_strategy
from utils import (
    AlreadyStamped,
    LoggingInfo,
    LoginFailedError,
    StampFailedError,
    get_chrome_options,
    gethotdealinfo,
    save_log_error,
)
from webdriverwrapper import Webdriverwrapper

logger = logging.getLogger("onadaily")


class StampResult(object):
    def __init__(self, site: Site) -> None:
        self.site = site
        self.passed = False
        self.iserror = False
        self.message = ""

    def __bool__(self) -> bool:
        return self.passed


class Onadaily(object):
    def __init__(self) -> None:
        self.passed: dict[Site, StampResult] = {}

        for site in options.sites:
            self.passed[site] = StampResult(site)
        self.keywordnoti = PrettyTable()
        self.keywordnoti.field_names = ["사이트", "품명", "정상가", "할인가"]

        self.last_exceptions: dict[Site, LoggingInfo] = {}

        options.load_settings()

    def initdriver(self) -> Webdriverwrapper:
        driver = Webdriverwrapper(
            get_chrome_options(
                options.datadir_required(),
                options.common.datadir,
                options.common.profile,
                options.common.headless,
            )
        )

        return driver

    def check(self, driver: Webdriverwrapper, site: Site) -> StampResult:
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

            if options.common.showhotdeal and site.hotdeal_table is not None:  # 핫딜 테이블 불러오기
                table = gethotdealinfo(driver.page_source, site)
                if table is not None:
                    print(table)

                    if len(options.common.keywordnoti) > 0:
                        keywordproducts = table.keywordcheck(options.common.keywordnoti)
                        if len(keywordproducts) > 0:
                            self.keywordnoti.add_rows(keywordproducts)

            stamp_strategy = get_stamp_strategy(site)
            stamp_strategy.stamp(driver, site)

            result.message = "✅ 출석 체크 성공"
            result.passed = True
        except AlreadyStamped as e:
            result.message = f"ℹ️ 이미 출첵함\n-{e}"
            result.passed = True
        except LoginFailedError as e:
            result.message = f"❌ 로그인 중 실패\n-{e}"
            result.iserror = True

        except StampFailedError as e:
            result.message = f"❌ 출석체크 중 실패\n-{e}"
            result.iserror = True
        except Exception as e:
            result.message = f"❌ 알 수 없는 오류\n-{e}"
            result.iserror = True
        finally:
            if result.iserror:
                result.passed = False
                self.last_exceptions[site] = LoggingInfo(site, driver)

        print(result.message)
        return result

    def run(self) -> None:
        retry_count = 0
        max_retries = options.common.retrytime if options.common.autoretry else 1

        while retry_count < max_retries and not all(self.passed.values()):
            retry_count += 1
            order = options.common.order

            with self.initdriver() as driver:
                for site in order:
                    self._currentsite = site
                    if self.passed[site]:
                        continue

                    self.passed[site] = self.check(driver, site)

        if all(self.passed.values()):
            if len(options.common.keywordnoti) > 0:
                print("======키워드 알림======")
                if len(self.keywordnoti.rows) > 0:
                    print(self.keywordnoti)
                else:
                    print("키워드 알림 없음")
        else:
            print("===============")
            print(f"❌ 재시도 {max_retries}번 실패")
            failedsites = [result.site for result in self.passed.values() if not result.passed]
            print(f"실패한 사이트 : {failedsites}")

            for failedsite in failedsites:
                if failedsite in self.last_exceptions:
                    save_log_error(self.last_exceptions[failedsite])

        print("======결과======")
        for result in self.passed.values():
            print(f"사이트 : {result.site.name} / {result.message}")
