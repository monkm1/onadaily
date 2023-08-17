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
from config import Site, options
from webdriverwrapper import Webdriverwrapper

if __name__ == "__main__":

    def remove_query(url) -> str:
        return urlunsplit(urlsplit(url)._replace(query="", fragment=""))

    def waitlogin(driver: Webdriverwrapper, site: Site):
        chkxpath = site.login_check_xpath
        driver.wait_for(chkxpath)

    def chklogined(driver: Webdriverwrapper, site: Site) -> bool:
        chkxpath = site.login_check_xpath
        ele = driver.find_xpath(chkxpath)
        if ele:
            return True
        return False

    def chkloginurl(driver: Webdriverwrapper, site: Site) -> bool:
        if site.name != "banana":
            if remove_query(driver.current_url) != site.login_url:
                return False
            return True
        else:
            if driver.find_elements(By.XPATH, "//div[text() = '회원 로그인']"):
                return True
            return False

    def printsiteconfig(driver: Webdriverwrapper, site: Site) -> None:
        print(f"site : {site}/{site.name}")
        print(f"enable : {site.enable}")
        print(f"login : {site.login}")
        print(f"datadir required : {options.datadir_required()}")
        print(f"current url : {driver.current_url}")

    def printhotdealinfo(page_source: str, site: Site):
        soup = BeautifulSoup(page_source, "html.parser")
        soup = soup.select_one(site.hotdeal_table).select_one("div")  # type: ignore
        products_all = soup.find_all("div", recursive=False)
        products = []
        for p in products_all:
            if p.has_attr("data-swiper-slide-index") and "swiper-slide-duplicate" not in p["class"]:
                productsoup = list(p.children)[1]

                price = dc_price = name = "이게 보이면 오류"
                if site.name == "onami":
                    dc_price = productsoup.find("p", "price").find("span").text
                    price = productsoup.find("strike").text
                    name = productsoup.find("p", "name").text

                elif site.name == "showdang":
                    price = productsoup.find("span", "or-price").text
                    dc_price = productsoup.find("span", "sl-price").text
                    name = productsoup.find("ul", "swiper-prd-info-name").text

                products.append(HotdealInfo(name, price, dc_price))

        table = PrettyTable()
        table.field_names = ["품명", "정상가", "할인가"]
        table.add_rows([x.to_row() for x in products])
        print(table)

    def login(driver: Webdriverwrapper, site: Site):
        if not chklogined(driver, site):
            if site.name != "banana":
                driver.get(site.login_url)

            if site.login == "default":
                idform = driver.wait_move_click(site.input_id)
                idform.send_keys(site.id)
                pwdform = driver.wait_move_click(site.input_pwd)
                pwdform.send_keys(site.password)  # write id and password

            driver.wait_move_click(site.btn_login)

            waitlogin(driver, site)

    def stamp(driver: Webdriverwrapper, site: Site) -> bool:
        try:
            driver.wait_move_click(site.btn_stamp)

            driver.wait_for_alert()
            alert = driver.switch_to.alert

            if site.name == "banana" and alert.text == "잠시후 다시 시도해 주세요." or alert.text == "이미 출석체크를 하셨습니다.":
                alert.accept()
                raise TimeoutException()

            alert.accept()
            return True
        except TimeoutException:
            return False

    def check(driver: Webdriverwrapper, site: Site) -> None:
        print(f"== {site.name} ==")

        if not site.enable:
            print("skip")
            return None

        driver.get(site.main_url)
        login(driver, site)
        print("로그인 성공")

        if options.common.showhotdeal and site.name != "banana" and site.name != "dingdong":
            printhotdealinfo(driver.page_source, site)

        driver.get(site.stamp_url)
        if stamp(driver, site):
            print("출석 체크 성공")
        else:
            print("출석체크 버튼을 찾을 수 없습니다. 이미 체크 했거나 오류입니다.")
        print()

    def get_chrome_options():
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
            datadir = path.expandvars(datadir)
            chromeoptions.add_argument(f"--user-data-dir={datadir}")
            chromeoptions.add_argument(f"--profile-directory={options.common.profile}")

        return chromeoptions

    # #########
    # main
    # #########
    passed = [False] * len(options.sites)
    autoretry = True
    retrytime = 0
    try:
        options.load_settings()
    except ConfigError as ex:
        print("설정 파일 오류 :\n", ex)
        autoretry = False
    except yaml.YAMLError:
        print("설정 파일 분석 중 오류 발생:")
        print(traceback.format_exc())
        autoretry = False

    while autoretry and not all(passed):
        try:
            retrytime += 1
            autoretry = options.common.autoretry
            order = options.common.order

            if retrytime > options.common.retrytime:
                print(f"재시도 {retrytime-1}번 실패")

                failedsites = []
                for i in range(len(order)):
                    if passed[i]:
                        continue
                    failedsites.append(consts.SITE_NAMES[i])
                print(f"실패한 사이트 : {failedsites}")
                autoretry = False
                break

            driver = Webdriverwrapper(get_chrome_options())
            for sitename in order:
                site = options.getsite(sitename)
                if passed[site.code]:
                    continue
                check(driver, site)
                passed[site.code] = True

            driver.quit()

            if all(passed):
                print("\n모든 출석 체크 완료")

        except WebDriverException:
            print("크롬 에러가 발생했습니다. 소셜 로그인을 사용하면 열려있는 크롬 창을 전부 닫고 실행해 주세요.")
            print(traceback.format_exc())
        except Exception:
            print(traceback.format_exc())
            if config._FILE_LOADED:
                printsiteconfig(driver, site)
        finally:
            try:
                driver.quit()
            except NameError:
                pass
            except Exception:
                print(traceback.format_exc())

    if options.common.entertoquit:
        input("종료하려면 Enter를 누르세요...")
