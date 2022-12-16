# consts
SETTING_FILE_NAME = "onadaily.yaml"
ONAMI = 0
SHOWDANG = 1
BANANA = 2
DINGDONG = 3
SITES = [ONAMI, SHOWDANG, BANANA, DINGDONG]
SITE_NAMES = ["onami", "showdang", "banana", "dingdong"]
URLS = [
    "https://oname.kr/index.html",
    "https://showdang.kr/",
    "https://www.bananamall.co.kr/",
    "https://www.dingdong.co.kr",
]
STAMP_URLS = [
    "https://oname.kr/attend/stamp.html",
    "https://showdang.kr/attend/stamp.html",
    "https://www.bananamall.co.kr/etc/attendance.php",
    "https://www.dingdong.co.kr/attend/stamp.html",
]
LOGIN_URLS = [
    "https://oname.kr/member/login.html",
    "https://showdang.kr/member/login.html",
    "https://www.bananamall.co.kr/",
    "https://dingdong.co.kr/member/login.html",
]
INPUT_ID = ['//*[@id="member_id"]', r'//*[@id="member_id"]', r"//*[@id='id']", "//input[@id='member_id']"]
INPUT_PWD = [
    '//*[@id="member_passwd"]',
    r'//*[@id="member_passwd"]',
    "//*[@id='passwd']",
    "//input[@id='member_passwd']",
]
CHK_LOGIN = [
    "//span[contains(@class, 'member-var-name') and string-length(text()) > 0]",
    "//span[contains(@class, 'member-var-name') and string-length(text()) > 0]",
    "//a[@title='로그아웃']",
    "//a[text()='로그아웃']",
]
BTN_LOGIN = [
    "//a[contains(@onclick, 'login')]",
    "//a[contains(@onclick, 'login')]",
    "//input[contains(@onclick, 'loginch')]",
    "//a[contains(@onclick, 'login')]/img",
]

BTN_GOOGLE_LOGIN = [
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'googleplus')]",
    "//a [contains(@onclick, 'snsLogin') and contains(@onclick,'google')]",
    "//a[contains(@href, 'google_login')]/img",
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'googleplus')]/img",
]
BTN_KAKAO_LOGIN = [
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'kakaosyncLogin')]",
    "//a [contains(@onclick, 'snsLogin') and contains(@onclick,'kakao')]",
    "//a[contains(@href, 'kakao_login')]/img",
    "//a [contains(@onclick, 'MemberAction') and contains(@onclick,'kakaosyncLogin')]/img",
]
BTN_NAVER_LOGIN = [
    None,
    None,
    "//a[contains(@href, 'naver_login')]/img",
    "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'naver')]/img",
]
BTN_FACEBOOK_LOGIN = [
    None,
    None,
    "//a[contains(@href, 'facebook_login')]/img",
    "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'facebook')]/img",
]
BTN_TWITTER_LOGIN = [None, None, "//a[contains(@href, 'twitter_login')]/img", None]

LOGIN = {
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
]
HOTDEAL_TABLE = [".ms-wrap", "#todaysale", None, ".ms-wrap"]
