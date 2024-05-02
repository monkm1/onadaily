# consts
from typing import Any, Dict

SETTING_FILE_NAME = "onadaily.yaml"
ONAMI = 0
SHOWDANG = 1
BANANA = 2
DINGDONG = 3
DOMAE = 4
SITES = [ONAMI, SHOWDANG, BANANA, DINGDONG, DOMAE]
SITE_NAMES = ["onami", "showdang", "banana", "dingdong", "domae"]
URLS = [
    "https://oname.kr/index.html",
    "https://showdang.kr/",
    "https://www.bananamall.co.kr/",
    "https://www.dingdong.co.kr",
    "https://domaedoll.com/",
]
STAMP_URLS = [
    "https://oname.kr/attend/stamp.html",
    "https://showdang.kr/attend/stamp.html",
    "https://www.bananamall.co.kr/etc/attendance.php",
    "https://www.dingdong.co.kr/attend/stamp.html",
    "https://domaedoll.com/attend/stamp.html",
]
LOGIN_URLS = [
    "https://oname.kr/member/login.html",
    "https://showdang.kr/member/login.html",
    "https://www.bananamall.co.kr/",
    "https://dingdong.co.kr/member/login.html",
    "https://domaedoll.com/intro/adult_im.html",
]
INPUT_ID = [
    '//*[@id="member_id"]',
    r'//*[@id="member_id"]',
    r"//*[@id='id']",
    "//input[@id='member_id']",
    "//input[@id='member_id']",
]
INPUT_PWD = [
    '//*[@id="member_passwd"]',
    r'//*[@id="member_passwd"]',
    "//*[@id='passwd']",
    "//input[@id='member_passwd']",
    "//input[@id='member_passwd']",
]
CHK_LOGIN = [
    "//span[contains(@class, 'member-var-name') and string-length(text()) > 0]",
    "//span[contains(@class, 'member-var-name') and string-length(text()) > 0]",
    "//a[@title='로그아웃']",
    "//a[text()='로그아웃']",
    "//a[contains(@data-ez-item, 'logout')]",
]
BTN_LOGIN = [
    "//a[contains(@onclick, 'login')]",
    "//a[contains(@onclick, 'login')]",
    "//input[contains(@onclick, 'loginch')]",
    "//a[contains(@onclick, 'login')]",
    "//a[contains(@onclick, 'MemberAction.login')]",
]

BTN_GOOGLE_LOGIN = [
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'googleplus')]",
    "//a [contains(@onclick, 'snsLogin') and contains(@onclick,'google')]",
    "//a[contains(@href, 'google_login')]/img",
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'googleplus')]/img",
    None,
]
BTN_KAKAO_LOGIN = [
    None,
    "//a [contains(@onclick, 'snsLogin') and contains(@onclick,'kakao')]",
    "//a[contains(@href, 'kakao_login')]/img",
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'kakaosyncLogin')]/img",
    None,
]
BTN_NAVER_LOGIN = [
    None,
    None,
    "//a[contains(@href, 'naver_login')]/img",
    "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'naver')]/img",
    None,
]
BTN_FACEBOOK_LOGIN = [
    None,
    None,
    "//a[contains(@href, 'facebook_login')]/img",
    "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'facebook')]/img",
    None,
]
BTN_TWITTER_LOGIN = [None, None, "//a[contains(@href, 'twitter_login')]/img", None, None]

LOGIN: Dict[str, Any] = {
    "default": BTN_LOGIN,
    "google": BTN_GOOGLE_LOGIN,
    "kakao": BTN_KAKAO_LOGIN,
    "naver": BTN_NAVER_LOGIN,
    "facebook": BTN_FACEBOOK_LOGIN,
    "twitter": BTN_TWITTER_LOGIN,
}
BTN_STAMP = [
    "//a[contains(@onclick, 'attend_send')]/img",
    "//a[contains(@onclick, 'attend_send')]",
    "//a[contains(@href, 'attendance_check')]",
    "//a[contains(@onclick, 'attend_send')]",
    "//a[contains(@onclick, 'attend_send')]",
]
HOTDEAL_TABLE: list[str | None] = [".ms-wrap", "#todaysale", None, None, None]

STAMP_CALENDAR: list[str] = [
    "table[class^=xans-element-]>tbody",
    "table[class^=xans-element-]>tbody",
    "table.calendar>tbody",
    "table[class^=xans-element-]>tbody",
    "table[class^=xans-element-]>tbody",
]
