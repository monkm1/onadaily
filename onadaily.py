import traceback

from prettytable import PrettyTable
from selenium.common import TimeoutException, WebDriverException

import config
from config import Site, options
from utils import ParseError, check_already_stamp, get_chrome_options, gethotdealinfo
from webdriverwrapper import Webdriverwrapper


class StampResult(object):
    def __init__(self, site: Site) -> None:
        self.site = site
        self.passed = False
        self.error = False
        self.message = ""

    def __bool__(self) -> bool:
        return self.passed


class Onadaily(object):
    def __init__(self) -> None:
        self.passed: dict[Site, StampResult] = {}

        for site in options.sites:
            self.passed[site] = StampResult(site)

        self.autoretry = True
        self.retrytime = 0
        self.keywordnoti = PrettyTable()
        self.keywordnoti.field_names = ["사이트", "품명", "정상가", "할인가"]

        options.load_settings()

    def run(self) -> None:
        def check(site: Site) -> StampResult:
            print(f"== {site.name} ==")
            result = StampResult(site)

            if not site.enable:
                print("skip")
                result.message = "스킵"
                result.passed = True
                return result

            self.driver.get(site.login_url)
            login(site)
            print("로그인 성공")

            if options.common.showhotdeal and site.name != "banana" and site.name != "dingdong":
                table = gethotdealinfo(self.driver.page_source, site)
                print(table)

                if len(options.common.keywordnoti) > 0:
                    keywordproducts = table.keywordcheck(options.common.keywordnoti)
                    if len(keywordproducts) > 0:
                        self.keywordnoti.add_rows(keywordproducts)

            self.driver.get(site.stamp_url)
            result = stamp(site)

            print(result.message)
            return result

        def login(site: Site) -> None:
            if not self.driver.check_logined(site):
                if site.name != "banana":
                    self.driver.get(site.login_url)

                if site.login == "default":
                    idform = self.driver.wait_move_click(site.input_id)
                    idform.send_keys(site.id)
                    pwdform = self.driver.wait_move_click(site.input_pwd)
                    pwdform.send_keys(site.password)  # write id and password

                self.driver.wait_move_click(site.btn_login)

                self.driver.wait_login(site)

        def stamp(site: Site) -> StampResult:
            try:
                result = StampResult(site)

                self.driver.wait_for_selector(site.stamp_calendar)
                if check_already_stamp(site, self.driver.page_source):
                    result.message = "이미 출첵함"
                    result.passed = True
                    return result
                self.driver.wait_move_click(site.btn_stamp)

                self.driver.wait_for_alert()
                alert = self.driver.switch_to.alert

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

        while self.autoretry and not all(self.passed.values()):
            try:
                self.retrytime += 1
                self.autoretry = options.common.autoretry
                order = options.common.order

                if self.retrytime > options.common.retrytime:
                    print(f"재시도 {self.retrytime-1}번 실패")
                    failedsites = [result.site.name for result in self.passed.values() if not result.passed]
                    print(f"실패한 사이트 : {failedsites}")
                    self.autoretry = False
                    break

                self.driver = Webdriverwrapper(
                    get_chrome_options(
                        options.datadir_required(),
                        options.common.datadir,
                        options.common.profile,
                        options.common.headless,
                    )
                )

                for site in order:
                    self._currentsite = site
                    if self.passed[site]:
                        continue

                    self.passed[site] = check(site)

                self.driver.quit()

                if all(self.passed.values()):
                    if len(options.common.keywordnoti) > 0:
                        print("======키워드 알림======")
                        if len(self.keywordnoti.rows) > 0:
                            print(self.keywordnoti)
                        else:
                            print("키워드 알림 없음")

            except WebDriverException:
                print("크롬 에러가 발생했습니다. 소셜 로그인을 사용하면 열려있는 크롬 창을 전부 닫고 실행해 주세요.")
                print(traceback.format_exc())
            except Exception:
                print(traceback.format_exc())
                if config._FILE_LOADED:
                    self.printsiteconfig(self._currentsite)
            finally:
                try:
                    self.driver.quit()
                except (NameError, AttributeError):
                    pass
                except Exception:
                    print(traceback.format_exc())

            print("======결과======")
            for result in self.passed.values():
                print(f"사이트 : {result.site.name} / {result.message}")

    def printsiteconfig(self, site: Site) -> None:
        print(f"site : {site.code}/{site.name}")
        print(f"enable : {site.enable}")
        print(f"login : {site.login}")
        print(f"datadir required : {options.datadir_required()}")
        print(f"current url : {self.driver.current_url}")
