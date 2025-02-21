import logging
import traceback
from time import sleep

from prettytable import PrettyTable
from selenium.common import TimeoutException, WebDriverException

from config import Site, options
from consts import BNA_LOGIN_WND_XPATH
from utils import ParseError, check_already_stamp, cleartextarea, get_chrome_options, gethotdealinfo
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
        print(f"== {site.name} ==")
        result = StampResult(site)

        if not site.enable:
            print("skip")
            result.message = "스킵"
            result.passed = True
            return result

        driver.get(site.login_url)
        self.login(driver, site)
        print("로그인 성공")

        if options.common.showhotdeal and site.hotdeal_table is not None:  # 핫딜 테이블 불러오기
            table = gethotdealinfo(driver.page_source, site)
            if table is not None:
                print(table)

                if len(options.common.keywordnoti) > 0:
                    keywordproducts = table.keywordcheck(options.common.keywordnoti)
                    if len(keywordproducts) > 0:
                        self.keywordnoti.add_rows(keywordproducts)

        driver.get(site.stamp_url)
        result = self.stamp(driver, site)

        print(result.message)
        return result

    def login(self, driver: Webdriverwrapper, site: Site) -> None:
        if not driver.check_logined(site):  # 로그인 상태 체크(로그인 이미 되어있는 경우 있음)
            current_window_handle = driver.current_window_handle
            if site.name != "banana":
                driver.get(site.login_url)
            else:
                driver.wait_move_click(BNA_LOGIN_WND_XPATH)

                another_window = list(set(driver.window_handles) - {driver.current_window_handle})[0]
                driver.switch_to.window(another_window)

                if driver.check_logined(site):
                    return

            if site.login == "default":
                idform = driver.wait_move_click(site.input_id)
                cleartextarea(idform)
                assert site.id is not None
                idform.send_keys(site.id)

                pwdform = driver.wait_move_click(site.input_pwd)
                cleartextarea(pwdform)
                assert site.password is not None
                pwdform.send_keys(site.password)  # write id and password

            driver.wait_move_click(site.btn_login)

            if site.name == "banana":
                driver.switch_to.window(current_window_handle)

            driver.wait_login(site)

    def stamp(self, driver: Webdriverwrapper, site: Site) -> StampResult:
        try:
            result = StampResult(site)

            driver.wait_for_selector(site.stamp_calendar)
            if check_already_stamp(site, driver.page_source):
                result.message = "이미 출첵함"
                result.passed = True
                return result
            if site.name == "onami":
                sleep(1)
            driver.wait_move_click(site.btn_stamp)

            driver.wait_for_alert()
            alert = driver.switch_to.alert

            print(f"메시지 : {alert.text}")

            if site.name == "banana":
                if alert.text == "잠시후 다시 시도해 주세요.":
                    alert.accept()
                    raise TimeoutException()
                elif alert.text == "이미 출석체크를 하셨습니다.":
                    raise ParseError("달력 파싱 오류")

            alert.accept()
            result.message = "출석 체크 성공"
            result.passed = True
            return result
        except TimeoutException:
            result.message = "출석 체크 버튼 찾지 못함"
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

                    try:
                        self.passed[site] = self.check(driver, site)

                    except WebDriverException:
                        self.passed[site].iserror = True
                        logger.exception(
                            "크롬 에러가 발생했습니다. 소셜 로그인을 사용하면 열려있는 크롬 창을 전부 닫고 실행해 주세요."
                        )
                        self.printsiteconfig(self._currentsite, driver)
                    except Exception:
                        self.passed[site].iserror = True
                        logger.exception("")
                        self.printsiteconfig(self._currentsite, driver)
                    finally:
                        if self.passed[site].iserror:
                            self.passed[site].message = "실패, 오류 출력 확인"

        if all(self.passed.values()):
            if len(options.common.keywordnoti) > 0:
                print("======키워드 알림======")
                if len(self.keywordnoti.rows) > 0:
                    print(self.keywordnoti)
                else:
                    print("키워드 알림 없음")
        else:
            print("===============")
            print(f"재시도 {max_retries}번 실패")
            failedsites = [result.site.name for result in self.passed.values() if not result.passed]
            print(f"실패한 사이트 : {failedsites}")

        print("======결과======")
        for result in self.passed.values():
            print(f"사이트 : {result.site.name} / {result.message}")

    def printsiteconfig(self, site: Site, driver: Webdriverwrapper) -> None:
        logger.info(f"site : {site.code}/{site.name}")
        logger.info(f"enable : {site.enable}")
        logger.info(f"login : {site.login}")
        logger.info(f"datadir required : {options.datadir_required()}")

        if driver is not None and not driver.quited:
            logger.info(f"Chrome version : {driver.capabilities['browserVersion']}")
