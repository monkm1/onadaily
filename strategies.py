import abc
import logging
from time import sleep

from selenium.webdriver.common.alert import Alert

from config import Site
from consts import BNA_LOGIN_WND_XPATH
from utils import (
    AlreadyStamped,
    LoginFailedError,
    ParseError,
    StampFailedError,
    check_already_stamp,
    handle_selenium_error,
)
from webdriverwrapper import Webdriverwrapper

logger = logging.getLogger("onadaily")


class BaseLoginStrategy(abc.ABC):
    def login(self, driver: Webdriverwrapper, site: Site) -> None:
        if driver.check_logined(site):
            logger.debug(f"{site.name} 로그인 이미 되어있음")
            return

        self._prepare_login(driver, site)
        self._enter_id_password(driver, site)
        self._click_login_button(driver, site)
        self._final_login(driver, site)

    def _prepare_login(self, driver: Webdriverwrapper, site: Site) -> None:
        driver.get(site.login_url)

    @handle_selenium_error(LoginFailedError, "ID/Password 입력 실패")
    def _enter_id_password(self, driver: Webdriverwrapper, site: Site) -> None:
        if site.login == "default":
            idform = driver.wait_move_click(site.input_id)
            driver.cleartextarea(idform)
            assert site.id is not None
            idform.send_keys(site.id)

            pwdform = driver.wait_move_click(site.input_pwd)
            driver.cleartextarea(pwdform)
            assert site.password is not None
            pwdform.send_keys(site.password)  # write id and password

    @handle_selenium_error(LoginFailedError, "로그인 버튼 클릭 실패")
    def _click_login_button(self, driver: Webdriverwrapper, site: Site) -> None:
        if site.btn_login is None:
            raise LoginFailedError(f"로그인 버튼 클릭 실패/{site.name}에서 지원하지 않는 로그인 방식입니다.")
        driver.wait_move_click(site.btn_login)

    @handle_selenium_error(LoginFailedError, "로그인 확인 실패")
    def _final_login(self, driver: Webdriverwrapper, site: Site) -> None:
        driver.wait_login(site)


class DefaultLoginStrategy(BaseLoginStrategy):
    pass


class BananaLoginStrategy(BaseLoginStrategy):
    def __init__(self) -> None:
        self.main_window_handle = ""

    @handle_selenium_error(LoginFailedError, "바나나 로그인 중 실패")
    def _prepare_login(self, driver: Webdriverwrapper, site: Site) -> None:
        super()._prepare_login(driver, site)

        self.main_window_handle = driver.current_window_handle
        driver.wait_move_click(BNA_LOGIN_WND_XPATH)

        another_window = list(set(driver.window_handles) - {driver.current_window_handle})[0]
        driver.switch_to.window(another_window)

    def _final_login(self, driver: Webdriverwrapper, site: Site) -> None:
        driver.switch_to.window(self.main_window_handle)
        return super()._final_login(driver, site)


def get_login_strategy(site: Site) -> BaseLoginStrategy:
    if site.name == "banana":
        return BananaLoginStrategy()
    else:
        return DefaultLoginStrategy()


class BaseStampStrategy(abc.ABC):
    def stamp(self, driver: Webdriverwrapper, site: Site):
        self._prepare_stamp(driver, site)
        calendar_page = self._get_calendar_source(driver, site)

        try:
            if check_already_stamp(site, calendar_page):
                raise AlreadyStamped(f"{site.name} : 이미 출첵함")
        except ParseError as ex:
            raise StampFailedError("달력 파싱 중 오류 발생") from ex

        self._click_stamp_button(driver, site)
        alert = self._get_alert(driver, site)
        self._handle_alert(alert)

    def _prepare_stamp(self, driver: Webdriverwrapper, site: Site) -> None:
        driver.get(site.stamp_url)

    @handle_selenium_error(StampFailedError, "달력 가져오기 실패")
    def _get_calendar_source(self, driver: Webdriverwrapper, site: Site) -> str:
        driver.wait_for_selector(site.stamp_calendar)
        return driver.page_source

    @handle_selenium_error(StampFailedError, "출첵 버튼 클릭 실패")
    def _click_stamp_button(self, driver: Webdriverwrapper, site: Site):
        if site.name == "onami":
            sleep(1)

        driver.wait_move_click(site.btn_stamp)

    @handle_selenium_error(StampFailedError, "얼럿 찾기 실패")
    def _get_alert(self, driver: Webdriverwrapper, site: Site) -> Alert:
        driver.wait_for_alert()
        alert = driver.switch_to.alert

        print(f"메시지 : {alert.text}")

        return alert

    @handle_selenium_error(StampFailedError, "얼럿 처리 실패")
    def _handle_alert(self, alert: Alert):
        alert.accept()


class DefaultStampStrategy(BaseStampStrategy):
    pass


class BananaStampStrategy(BaseStampStrategy):
    def _handle_alert(self, alert: Alert):
        alert_text = alert.text
        alert.accept()
        if alert_text == "잠시후 다시 시도해 주세요.":
            raise StampFailedError("바나나 얼럿 처리 실패/알 수 없는 이유")
        elif alert_text == "이미 출석체크를 하셨습니다.":
            raise StampFailedError("바나나 얼럿 처리 실패/달력 파싱 오류")


def get_stamp_strategy(site: Site) -> BaseStampStrategy:
    if site.name == "banana":
        return BananaStampStrategy()
    else:
        return DefaultStampStrategy()
