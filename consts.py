# consts
SETTING_FILE_NAME = "onadaily.yaml"
ONAMI = 0
SHOWDANG = 1
BANANA = 2
DINGDONG = 3
DOMAE = 4
SITES = [ONAMI, SHOWDANG, BANANA, DINGDONG, DOMAE]
SITE_NAMES = ["onami", "showdang", "banana", "dingdong", "domae"]
URLS = {
    "onami": "https://oname.kr/index.html",
    "showdang": "https://showdang.co.kr/",
    "banana": "https://www.bananamall.co.kr/",
    "dingdong": "https://www.dingdong.co.kr",
    "domae": "https://domaedoll.com/",
}
STAMP_URLS = {
    "onami": "https://oname.kr/attend/stamp2.html",
    "showdang": "https://showdang.co.kr/event/attend_stamp.php",
    "banana": "https://www.bananamall.co.kr/etc/attendance.php",
    "dingdong": "https://www.dingdong.co.kr/attend/stamp.html",
    "domae": "https://domaedoll.com/attend/stamp.html",
}
LOGIN_URLS = {
    "onami": "https://oname.kr/member/login.html",
    "showdang": "https://showdang.co.kr/member/login.php",
    "banana": "https://www.bananamall.co.kr/",
    "dingdong": "https://dingdong.co.kr/member/login.html",
    "domae": "https://domaedoll.com/intro/adult_im.html",
}
INPUT_ID = {
    "onami": '//*[@id="member_id"]',
    "showdang": r'//*[@id="loginId"]',
    "banana": r"//*[@name='id']",
    "dingdong": "//input[@id='member_id']",
    "domae": "//input[@id='member_id']",
}
INPUT_PWD = {
    "onami": '//*[@id="member_passwd"]',
    "showdang": r'//*[@id="loginPwd"]',
    "banana": "//*[@name='passwd']",
    "dingdong": "//input[@id='member_passwd']",
    "domae": "//input[@id='member_passwd']",
}
CHK_LOGIN = {
    "onami": "//span[contains(@class, 'member-var-name') and string-length(text()) > 0]",
    "showdang": "//a[text()='LOGOUT']",
    "banana": "//a[@title='로그아웃']",
    "dingdong": "//a[text()='로그아웃']",
    "domae": "//a[text()='로그아웃']",
}
BTN_LOGIN = {
    "onami": "//a[contains(@onclick, 'login')]",
    "showdang": "//button[contains(@class, 'member_login')]",
    "banana": "//a[contains(@onclick, 'loginch')]",
    "dingdong": "//a[contains(@onclick, 'login')]",
    "domae": "//button[contains(@onclick, 'MemberAction.login')]",
}

BTN_GOOGLE_LOGIN = {
    "onami": "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'googleplus')]",
    "showdang": "//a[contains(@class,'btn_google_login')]",
    "banana": "//a[contains(@onclick, 'google_login')]/img",
    "dingdong": "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'googleplus')]/img",
    "domae": None,
}
BTN_KAKAO_LOGIN = {
    "onami": None,
    "showdang": "//a[contains(@class, 'btn_kakao_login')]",
    "banana": None,
    "dingdong": "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'kakaosyncLogin')]/img",
    "domae": None,
}
BTN_NAVER_LOGIN = {
    "onami": None,
    "showdang": "//a[contains(@class, 'btn_naver_login')]",
    "banana": "//a[contains(@onclick, 'naver_login')]/img",
    "dingdong": "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'naver')]/img",
    "domae": None,
}
BTN_FACEBOOK_LOGIN = {
    "onami": None,
    "showdang": None,
    "banana": "//a[contains(@href, 'facebook_login')]/img",
    "dingdong": "//a[contains(@onclick, 'MemberAction') and contains(@onclick,'facebook')]/img",
    "domae": None,
}
BTN_TWITTER_LOGIN = {
    "onami": None,
    "showdang": None,
    "banana": "//a[contains(@onclick, 'twitter_login')]/img",
    "dingdong": None,
    "domae": None,
}

LOGIN: dict[str, dict[str, str] | dict[str, str | None]] = {
    "default": BTN_LOGIN,
    "google": BTN_GOOGLE_LOGIN,
    "kakao": BTN_KAKAO_LOGIN,
    "naver": BTN_NAVER_LOGIN,
    "facebook": BTN_FACEBOOK_LOGIN,
    "twitter": BTN_TWITTER_LOGIN,
}
BTN_STAMP = {
    "onami": "//a[contains(@onclick, 'attend_send')]/img",
    "showdang": "//button[contains(@class, 'btn_attend_check')]",
    "banana": "//a[contains(@href, 'attendance_check')]",
    "dingdong": "//a[contains(@onclick, 'attend_send')]",
    "domae": "//a[contains(@onclick, 'attend_send')]",
}
HOTDEAL_TABLE: dict[str, str | None] = {
    "onami": ".ms-wrap",
    "showdang": "#todaysale",
    "banana": None,
    "dingdong": None,
    "domae": None,
}

STAMP_CALENDAR: dict[str, str] = {
    "onami": "table[class^=xans-element-]>tbody",
    "showdang": ".calendar_sec > table >tbody",
    "banana": "table.calendar>tbody",
    "dingdong": "table[class^=xans-element-]>tbody",
    "domae": "div.xans-attend-calendar>table>tbody",
}

BNA_LOGIN_WND_XPATH = "//a[@title='로그인']"
