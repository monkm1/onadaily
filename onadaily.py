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
from Webdriverwrapper import Webdriverwrapper

if __name__ == "__main__":

    def remove_query(url):
        return urlunsplit(urlsplit(url)._replace(query="", fragment=""))

    def waitlogin(driver, site):
        chkxpath = consts.CHK_LOGIN[site]
        driver.wait_for(chkxpath)

    def chklogined(driver, site):
        chkxpath = consts.CHK_LOGIN[site]
        ele = driver.find_xpath(chkxpath)
        if ele:
            return True
        return False

    def chkloginurl(driver, site):
        if site != consts.BANANA:
            if remove_query(driver.current_url) != consts.LOGIN_URLS[site]:
                return False
            return True
        else:
            if driver.find_elements(By.XPATH, "//div[text() = '회원 로그인']"):
                return True
            return False

    def printsiteconfig(driver, site):
        print(f"site : {site}/{consts.SITE_NAMES[site]}")
        print(f"enable : {getoption(site, 'enable')}")
        print(f"login : {getoption(site, 'login')}")
        print(f"datadir required : {datadir_required()}")
        print(f"current url : {driver.current_url}")

    def printhotdealinfo(page_source, site):
        soup = BeautifulSoup(page_source, "html.parser")
        soup = soup.select_one(consts.HOTDEAL_TABLE[site])
        products_all = soup.find_all("div")
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

                elif site == consts.DINGDONG:
                    pricesoup = productsoup.find("ul", "xans-element-").find_all("li")
                    reward = ""
                    for p in pricesoup:
                        if p.text.strip().startswith("회원가"):
                            price = p.find("span", recursive=False).text
                        elif p.text.strip().startswith("반짝할인"):
                            dc_price = p.find("span", recursive=False).text
                        elif p.text.strip().startswith("적립금"):
                            reward = p.find("span", recursive=False).text

                    if dc_price == "이게 보이면 오류":
                        dc_price = "(적립금)" + reward

                    name = productsoup.find("p", "name").find(text=True, recursive=False)

                products.append(HotdealInfo(name, price, dc_price))

        table = PrettyTable()
        table.field_names = ["품명", "정상가", "할인가"]
        table.add_rows([x.to_row() for x in products])
        print(table)

    def login(driver, site):
        if not chklogined(driver, site):
            if site != consts.BANANA:
                driver.get(consts.LOGIN_URLS[site])

            loginxpath = ""
            if getoption(site, "login") == "default":
                idform = driver.wait_move_click(consts.INPUT_ID[site])
                idform.send_keys(getoption(site, "id"))
                pwdform = driver.wait_move_click(consts.INPUT_PWD[site])
                pwdform.send_keys(getoption(site, "password"))  # write id and password

                loginxpath = consts.BTN_LOGIN[site]
            elif getoption(site, "login") == "kakao":
                loginxpath = consts.BTN_KAKAO_LOGIN[site]
            elif getoption(site, "login") == "google":
                loginxpath = consts.BTN_GOOGLE_LOGIN[site]
            driver.wait_move_click(loginxpath)

            waitlogin(driver, site)

    def stamp(driver, site):
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

    def check(driver, site):
        print(f"== {consts.SITE_NAMES[site]} ==")

        if getoption(site, "enable") is False:
            print("skip")
            return None

        driver.get(consts.URLS[site])
        login(driver, site)
        print("로그인 성공")

        if getoption("common", "showhotdeal") and site != consts.BANANA:
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

        for site in consts.SITES:
            check(driver, site)
        print("\n모든 출석 체크 완료")

    except ConfigError as ex:
        print("설정 파일 오류 :\n", ex)
    except WebDriverException:
        print("크롬 에러가 발생했습니다. 구글/카카오 로그인을 사용하면 열려있는 크롬 창을 전부 닫고 실행해 주세요.")
        print(traceback.format_exc())
    except yaml.YAMLError as ex:
        # from https://stackoverflow.com/questions/30269723/how-to-get-details-from-pyyaml-exception
        print("설정 파일 분석 중 오류 발생:")
        if hasattr(ex, "problem_mark"):
            if ex.context is not None:
                print(
                    "  parser says\n"
                    + str(ex.problem_mark)
                    + "\n  "
                    + str(ex.problem)
                    + " "
                    + str(ex.context)
                    + "\n수정 후 다시 실행해 주세요."
                )
            else:
                print("  parser says\n" + str(ex.problem_mark) + "\n  " + str(ex.problem) + "\n수정 후 다시 실행해 주세요.")
        else:
            print("설정 파일 로딩에 알 수 없는 오류가 발생했습니다.")
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
