import traceback
import typing
from datetime import datetime
from math import ceil
from os import path

import pytz
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options

import config
from config import Site, options
from webdriverwrapper import Webdriverwrapper


class StampResult(object):
    def __init__(self, site: Site):
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

                self.driver = Webdriverwrapper(self.get_chrome_options())

                for site in order:
                    self._currentsite = site
                    if self.passed[site]:
                        continue

                    self.passed[site] = self.check(site)

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

    def check(self, site: Site) -> StampResult:
        print(f"== {site.name} ==")
        result = StampResult(site)

        if not site.enable:
            print("skip")
            result.message = "스킵"
            return result

        self.driver.get(site.main_url)
        self.login(site)
        print("로그인 성공")

        if options.common.showhotdeal and site.name != "banana" and site.name != "dingdong":
            table = self.driver.gethotdealinfo(site)
            print(table)

            if len(options.common.keywordnoti) > 0:
                keywordproducts = table.keywordcheck(options.common.keywordnoti)
                if len(keywordproducts) > 0:
                    self.keywordnoti.add_rows(keywordproducts)

        self.driver.get(site.stamp_url)
        result = self.stamp(site)

        print(result.message)
        return result

    def login(self, site: Site) -> None:
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

    def stamp(self, site: Site) -> StampResult:
        try:
            self.driver.wait_for_selector(site.stamp_calendar)
            result = StampResult(site)
            if self.check_already_stamp(site, self.driver.page_source):
                result.message = "이미 출첵함"
                result.passed = True
                return result
            self.driver.wait_move_click(site.btn_stamp)

            self.driver.wait_for_alert()
            alert = self.driver.switch_to.alert

            if site.name == "banana" and alert.text == "잠시후 다시 시도해 주세요." or alert.text == "이미 출석체크를 하셨습니다.":
                alert.accept()
                raise TimeoutException()

            alert.accept()
            result.message = "출석 체크 성공"
            result.passed = True
            return result
        except TimeoutException:
            result.message = "출석 체크 버튼 찾지 못함"
            return result

    @typing.no_type_check
    def check_already_stamp(self, site: Site, source: str) -> bool:
        self.driver.wait_for_selector(site.stamp_calendar)
        soup = BeautifulSoup(source, "html.parser")
        tablesoup = soup.select_one(site.stamp_calendar)

        week, day = self.num_of_month_week()

        weekssoup = tablesoup.find_all(True, recursive=False)
        weeksoup = weekssoup[week - 1].find_all(True, recursive=False)

        todaysoup = weeksoup[day - 1]

        if site.name != "banana":
            if todaysoup.find("img", {"alt": "출석"}) is None:
                return False
            else:
                return True
        else:
            if todaysoup.find("img") is None:
                return False
            else:
                return True

    def get_chrome_options(self) -> Options:
        chromeoptions = Options()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"  # noqa
        chromeoptions.add_argument("user-agent=" + user_agent)
        chromeoptions.add_argument("--disable-extensions")
        chromeoptions.add_argument("--log-level=3")

        if options.common.headless:
            chromeoptions.add_argument("--disable-gpu")
            chromeoptions.add_argument("--headless")
            chromeoptions.add_argument("--window-size=1920,1080")
            chromeoptions.add_argument("--no-sandbox")
            chromeoptions.add_argument("--start-maximized")
            chromeoptions.add_argument("--disable-setuid-sandbox")
        if options.datadir_required():
            datadir = options.common.datadir
            if datadir is None:
                raise ValueError()
            datadir = path.expandvars(datadir)
            chromeoptions.add_argument(f"--user-data-dir={datadir}")
            chromeoptions.add_argument(f"--profile-directory={options.common.profile}")

        return chromeoptions

    def printsiteconfig(self, site: Site) -> None:
        print(f"site : {site.code}/{site.name}")
        print(f"enable : {site.enable}")
        print(f"login : {site.login}")
        print(f"datadir required : {options.datadir_required()}")
        print(f"current url : {self.driver.current_url}")

    def num_of_month_week(self) -> tuple[int, int]:
        utcnow = pytz.utc.localize(datetime.utcnow())
        date = utcnow.astimezone(pytz.timezone("Asia/Seoul"))

        date = datetime.today()
        first_day = date.replace(day=1)

        day_of_month = date.day

        if first_day.weekday() == 6:
            adjusted_dom = (1 + first_day.weekday()) / 7
        else:
            adjusted_dom = day_of_month + first_day.weekday()

        weeknum = int(ceil(adjusted_dom / 7.0))
        dayofweeknum = (date.weekday() + 1) % 7 + 1

        return weeknum, dayofweeknum
