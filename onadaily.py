import sys
import traceback
from os import path
from urllib.parse import urlsplit, urlunsplit

import yaml
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# consts
SETTING_FILE_NAME = "onadaily.yaml"
ONAMI = 0
SHOWDANG = 1
BANANA = 2
SITES = [ONAMI, SHOWDANG, BANANA]
SITE_NAMES = ["onami", "showdang", "banana"]
URLS = [
    "https://oname.kr/index.html",
    "https://showdang.kr/",
    "https://www.bananamall.co.kr/",
]
STAMP_URLS = [
    "https://oname.kr/attend/stamp.html",
    "https://showdang.kr/attend/stamp.html",
    "https://www.bananamall.co.kr/etc/attendance.php",
]
LOGIN_URLS = [
    "https://oname.kr/intro/adult_im.html",
    "https://showdang.kr/intro/adult_im.html",
    "https://www.bananamall.co.kr/",
]
INPUT_ID = ['//*[@id="member_id"]', r'//*[@id="member_id"]', r"//*[@id='id']"]
INPUT_PWD = [
    '//*[@id="member_passwd"]',
    r'//*[@id="member_passwd"]',
    "//*[@id='passwd']",
]
BTN_MAIN_LOGIN = [
    "/html/body/div[3]/div[1]/ul/li[1]/a",
    "/html/body/div[5]/div[1]/div/div/a[4]",
    "//a[@title='로그인' and contains(@href, 'login_start')]",
]
CHK_LOGIN = [
    "/html/body/div[3]/div[1]/div/b[1]/span[string-length(text()) > 0]",
    "/html/body/div[5]/div[1]/div/div/span[2]/strong/span[string-length(text()) > 0]",
    "/html/body/div[8]/div[1]/div[2]/div/div[2]/ul/li[2]/a[@title='로그아웃']",
]
BTN_LOGIN = [
    "//a[contains(@onclick, 'login')]",
    "//a[contains(@onclick, 'login')]",
    "//input[contains(@onclick, 'loginch')]",
]
BTN_GOOGLE_LOGIN = [
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'googleplus')]",
    "//a [contains(@onclick, 'snsLogin') and contains(@onclick,'google')]",
    "//a[contains(@href, 'google_login')]/img",
]
BTN_KAKAO_LOGIN = [
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'kakaosyncLogin')]",
    "//a [contains(@onclick, 'snsLogin') and contains(@onclick,'kakao')]",
    "//a[contains(@href, 'kakao_login')]/img",
]
BTN_STAMP = [
    "//a[contains(@onclick, 'attend_send')]/img",
    "//a[contains(@onclick, 'attend_send')]",
    "/html/body/div[8]/div[2]/div[6]/div[2]/div[1]/div/a",
]


if __name__ == "__main__":

    class YamlError(Exception):
        pass

    def getoption(site, option):
        section = "common"
        if site != "common":
            section = SITE_NAMES[site]
        return settings[section][option]

    def datadir_required():
        checklist = []
        for site in SITES:
            if getoption(site, "enable") is True:
                checklist.append(getoption(site, "login") != "default")
        return any(checklist)

    def check_yaml_valid():
        if datadir_required():
            if getoption("common", "datadir") is None or getoption("common", "profile") is None:
                print("구글/카카오 로그인을 사용하려면 설정 파일의 datadir, profile을 지정해 주세요.")
                raise YamlError()

        for site in SITES:
            if getoption(site, "enable") is True and getoption(site, "login") == "default":
                if getoption(site, "id") is None or getoption(site, "password") is None:
                    print(f"설정 파일의 {SITE_NAMES[site]} 아이디와 패스워드를 지정해 주세요.")
                    raise YamlError()

    def remove_query(url):
        return urlunsplit(urlsplit(url)._replace(query="", fragment=""))

    def waitlogin(driver, site):
        chkxpath = CHK_LOGIN[site]
        wait.until(EC.presence_of_element_located((By.XPATH, chkxpath)))

    def chklogined(driver, site):
        chkxpath = CHK_LOGIN[site]
        ele = driver.find_elements(By.XPATH, chkxpath)
        if ele:
            return True
        return False

    def chkloginurl(driver, site):
        if site != BANANA:
            if remove_query(driver.current_url) != LOGIN_URLS[site]:
                return False
            return True
        else:
            if driver.find_elements(By.XPATH, "//div[text() = '회원 로그인']"):
                return True
            return False

    def printsiteconfig(driver, site):
        print(f"site : {site}/{SITE_NAMES[site]}")
        print(f"enable : {getoption(site, 'enable')}")
        print(f"login : {getoption(site, 'login')}")
        print(f"datadir required : {datadir_required()}")
        print(f"current url : {driver.current_url}")

    def login(driver, site):
        if not chklogined(driver, site):
            if not chkloginurl(driver, site):
                mainlogin = wait.until(EC.presence_of_element_located((By.XPATH, BTN_MAIN_LOGIN[site])))
                mainlogin.click()

            try:
                loginxpath = ""
                if getoption(site, "login") == "default":
                    idform = wait.until(EC.presence_of_element_located((By.XPATH, INPUT_ID[site])))
                    pwdform = driver.find_element(By.XPATH, INPUT_PWD[site])
                    idform.send_keys(getoption(site, "id"))
                    pwdform.send_keys(getoption(site, "password"))  # write id and password

                    loginxpath = BTN_LOGIN[site]
                elif getoption(site, "login") == "kakao":
                    loginxpath = BTN_KAKAO_LOGIN[site]
                elif getoption(site, "login") == "google":
                    loginxpath = BTN_GOOGLE_LOGIN[site]

                loginbtn = wait.until(EC.presence_of_element_located((By.XPATH, loginxpath)))
                loginbtn.click()
            except TimeoutException:
                if driver.current_url != STAMP_URLS[site]:
                    raise

            waitlogin(driver, site)

    def stamp(driver, site):
        try:
            checkbtn = wait.until(EC.presence_of_element_located((By.XPATH, BTN_STAMP[site])))
            checkbtn.click()

            if site == ONAMI or site == SHOWDANG or site == BANANA:
                wait.until(EC.alert_is_present())
                alert = driver.switch_to.alert

                if site == BANANA and alert.text == "잠시후 다시 시도해 주세요." or alert.text == "이미 출석체크를 하셨습니다.":
                    alert.accept()
                    raise TimeoutException()

                alert.accept()
            return True
        except TimeoutException:
            return False

    def check(driver, site):
        print(f"== {SITE_NAMES[site]} ==")

        if getoption(site, "enable") is False:
            print("skip")
            return None

        driver.get(URLS[site])
        # driver.implicitly_wait(3)
        login(driver, site)
        print("로그인 성공")

        driver.get(STAMP_URLS[site])
        if stamp(driver, site):
            print("출석 체크 성공")
        else:
            print("출석체크 버튼을 찾을 수 없습니다. 이미 체크 했거나 오류입니다.")
        print()

    # #########
    # main
    # #########

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "test":  # test mode
            SETTING_FILE_NAME = "test.yaml"

        settings = {}
        with open(SETTING_FILE_NAME) as f:  # load yaml
            settings = dict(yaml.safe_load(f))

        check_yaml_valid()

        options = Options()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"  # noqa
        options.add_argument("user-agent=" + user_agent)
        options.add_argument("--disable-extensions")
        options.add_argument("--log-level=3")
        # options.add_argument("--window-size=300,300")
        if datadir_required():
            datadir = getoption("common", "datadir")
            datadir = path.expandvars(datadir)
            options.add_argument(f"--user-data-dir={datadir}")
            options.add_argument(f"--profile-directory={getoption('common', 'profile')}")

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 3)

        for site in SITES:
            check(driver, site)
        print("\n모든 출석 체크 완료")

    except YamlError:
        pass
    except Exception:
        print(traceback.format_exc())
        printsiteconfig(driver, site)
    finally:
        try:
            driver.quit()
        except NameError:
            pass
        except Exception:
            print(traceback.format_exc())

        if getoption("common", "entertoquit"):
            input("종료하려면 Enter를 누르세요...")
