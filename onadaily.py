import traceback
from os import path
from urllib.parse import urlsplit, urlunsplit

import yaml
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import config
import consts
from classes import ConfigError, HotdealInfo
from config import datadir_required, getoption, load_settings
from webdriverwrapper import Webdriverwrapper

if __name__ == "__main__":

    def remove_query(url) -> str:
        return urlunsplit(urlsplit(url)._replace(query="", fragment=""))

    def waitlogin(driver: Webdriverwrapper, site: int):
        chkxpath = consts.CHK_LOGIN[site]
        driver.wait_for(chkxpath)

    def chklogined(driver: Webdriverwrapper, site: int) -> bool:
        chkxpath = consts.CHK_LOGIN[site]
        ele = driver.find_xpath(chkxpath)
        if ele:
            return True
        return False

    def chkloginurl(driver: Webdriverwrapper, site: int) -> bool:
        if site != consts.BANANA:
            if remove_query(driver.current_url) != consts.LOGIN_URLS[site]:
                return False
            return True
        else:
            if driver.find_elements(By.XPATH, "//div[text() = '회원 로그인']"):
                return True
            return False

    def printsiteconfig(driver: Webdriverwrapper, site: int) -> None:
        print(f"site : {site}/{consts.SITE_NAMES[site]}")
        print(f"enable : {getoption(site, 'enable')}")
        print(f"login : {getoption(site, 'login')}")
        print(f"datadir required : {datadir_required()}")
        print(f"current url : {driver.current_url}")

    def printhotdealinfo(page_source: str, site: int):
        soup = BeautifulSoup(page_source, "html.parser")
        soup = soup.select_one(consts.HOTDEAL_TABLE[site]).select_one("div")
        products_all = soup.find_all("div", recursive=False)
        products = []
        for p in products_all:
            if p.has_attr("data-swiper-slide-index") and "swiper-slide-duplicate" not in p["class"]:
                productsoup = list(p.children)[1]

                price = dc_price = name = "이게 보이면 오류"
                if site == consts.ONAMI:
                    dc_price = productsoup.find("p", "price").find("span").text
                    price = productsoup.find("strike").text
                    name = productsoup.find("p", "name").text

                elif site == consts.SHOWDANG:
                    price = productsoup.find("span", "or-price").text
                    dc_price = productsoup.find("span", "sl-price").text
                    name = productsoup.find("ul", "swiper-prd-info-name").text

                products.append(HotdealInfo(name, price, dc_price))

        table = PrettyTable()
        table.field_names = ["품명", "정상가", "할인가"]
        table.add_rows([x.to_row() for x in products])
        print(table)

    def login(driver: Webdriverwrapper, site: int):
        if not chklogined(driver, site):
            if site != consts.BANANA:
                driver.get(consts.LOGIN_URLS[site])

            loginxpath = ""
            loginoption = getoption(site, "login")
            if loginoption == "default":
                idform = driver.wait_move_click(consts.INPUT_ID[site])
                idform.send_keys(getoption(site, "id"))
                pwdform = driver.wait_move_click(consts.INPUT_PWD[site])
                pwdform.send_keys(getoption(site, "password"))  # write id and password

                loginxpath = consts.LOGIN["default"][site]
            else:
                loginxpath = consts.LOGIN[loginoption][site]
            driver.wait_move_click(loginxpath)

            waitlogin(driver, site)

    def stamp(driver: Webdriverwrapper, site: int) -> bool:
        try:
            driver.wait_move_click(consts.BTN_STAMP[site])

            driver.wait_for_alert()
            alert = driver.switch_to.alert

            if site == consts.BANANA and alert.text == "잠시후 다시 시도해 주세요." or alert.text == "이미 출석체크를 하셨습니다.":
                alert.accept()
                raise TimeoutException()

            alert.accept()
            return True
        except TimeoutException:
            return False

    def check(driver: Webdriverwrapper, site: int):
        print(f"== {consts.SITE_NAMES[site]} ==")

        if getoption(site, "enable") is False:
            print("skip")
            return None

        driver.get(consts.URLS[site])
        login(driver, site)
        print("로그인 성공")

        if getoption("common", "showhotdeal") and site != consts.BANANA and site != consts.DINGDONG:
            printhotdealinfo(driver.page_source, site)

        driver.get(consts.STAMP_URLS[site])
        if stamp(driver, site):
            print("출석 체크 성공")
        else:
            print("출석체크 버튼을 찾을 수 없습니다. 이미 체크 했거나 오류입니다.")
        print()

    def get_chrome_options():
        options = Options()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"  # noqa
        options.add_argument("user-agent=" + user_agent)
        options.add_argument("--disable-extensions")
        options.add_argument("--log-level=3")

        if getoption("common", "headless"):
            options.add_argument("--disable-gpu")
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-setuid-sandbox")
        if datadir_required():
            datadir = getoption("common", "datadir")
            datadir = path.expandvars(datadir)
            options.add_argument(f"--user-data-dir={datadir}")
            options.add_argument(f"--profile-directory={getoption('common', 'profile')}")

        return options

    # #########
    # main
    # #########

    try:
        load_settings()
        driver = Webdriverwrapper(get_chrome_options())
        order = getoption("common", "order")
        order = [consts.SITE_DICTS[x] for x in order]

        for site in order:
            check(driver, site)

        print("\n모든 출석 체크 완료")

    except ConfigError as ex:
        print("설정 파일 오류 :\n", ex)
    except WebDriverException:
        print("크롬 에러가 발생했습니다. 구글/카카오 로그인을 사용하면 열려있는 크롬 창을 전부 닫고 실행해 주세요.")
        print(traceback.format_exc())
    except yaml.YAMLError:
        print("설정 파일 분석 중 오류 발생:")
        print(traceback.format_exc())
    except Exception:
        print(traceback.format_exc())
        if config.FILE_LOADED:
            printsiteconfig(driver, site)
    finally:
        try:
            driver.quit()
        except NameError:
            pass
        except Exception:
            print(traceback.format_exc())

    if config.entertoquit():
        input("종료하려면 Enter를 누르세요...")
