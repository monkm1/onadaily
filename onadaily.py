import sys
from os import path

import yaml
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

if __name__ == "__main__":

    # consts
    SETTING_FILE_NAME = "onadaily.yaml"
    ONAMI = 0
    SHOWDANG = 1
    SITES = [ONAMI, SHOWDANG]
    SITE_NAMES = ["onami", "showdang"]
    URLS = [
        "https://oname.kr/attend/stamp.html",
        "https://showdang.kr/intro/adult_im.html?returnUrl=%2Fattend%2Fstamp.html",
    ]
    STAMP_URLS = ["https://oname.kr/attend/stamp.html", "https://showdang.kr/attend/stamp.html"]
    INPUT_ID = ['//*[@id="member_id"]', r'//*[@id="member_id"]']
    INPUT_PWD = ['//*[@id="member_passwd"]', r'//*[@id="member_passwd"]']
    BTN_LOGIN = ["/html/body/div[3]/div[2]/div/div/form/div/div[1]/fieldset/a", "/html/body/div[1]/form/div/fieldset/a"]
    BTN_GOOGLE_LOGIN = [
        "/html/body/div[4]/div/form/div/div/fieldset/ul[2]/li[3]/a",
        "/html/body/div[1]/form/div/ul/li[4]/a",
    ]
    BTN_KAKAO_LOGIN = [
        "/html/body/div[3]/div[2]/div/div/form/div/div[2]/ul/li[4]/a",
        "/html/body/div[1]/form/div/ul/li[3]/a",
    ]
    BTN_CHECK = [
        "/html/body/div[4]/div/div[3]/form/div/div[1]/span/a",
        "/html/body/div[6]/div/div/div[3]/div/ul[2]/form/div/div[1]/span/a",
    ]

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        SETTING_FILE_NAME = "test.yaml"

    settings = {}
    with open(SETTING_FILE_NAME) as f:
        settings = dict(yaml.safe_load(f))

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
        return all(checklist)

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

    def check(site):
        print(f"== {SITE_NAMES[site]} ==")

        if getoption(site, "enable") is False:
            print("skip")
            return None

        driver.get(URLS[site])
        if site == ONAMI:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
        loginxpath = ""

        if getoption(site, "login") == "default":
            idform = driver.find_element(By.XPATH, INPUT_ID[site])
            pwdform = driver.find_element(By.XPATH, INPUT_PWD[site])
            idform.send_keys(getoption(site, "id"))
            pwdform.send_keys(getoption(site, "password"))

            loginxpath = BTN_LOGIN[site]
        elif getoption(site, "login") == "kakao":
            loginxpath = BTN_KAKAO_LOGIN[site]
        elif getoption(site, "login") == "google":
            loginxpath = BTN_GOOGLE_LOGIN[site]

        loginbtn = wait.until(EC.presence_of_element_located((By.XPATH, loginxpath)))
        loginbtn.click()
        WebDriverWait(driver, 10).until(lambda driver: driver.current_url == STAMP_URLS[site])
        print("로그인 성공")
        try:
            checkbtn = wait.until(EC.presence_of_element_located((By.XPATH, BTN_CHECK[site])))
            checkbtn.click()
            print("출석 체크 성공")
            if site == ONAMI:
                wait.until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert.accept()
        except TimeoutException:
            print("출석체크 버튼을 찾을 수 없습니다. 이미 체크 했거나 오류입니다.")
        print()

    for site in SITES:
        check(site)
    print("출석 체크 완료")
    driver.quit()

    if getoption("common", "entertoquit"):
        input("종료하려면 Enter를 누르세요...")
