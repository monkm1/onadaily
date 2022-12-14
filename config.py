import sys

import yaml

import consts
from classes import ConfigError

FILE_LOADED = False
settings = {}


def getoption(site: int, option: str):
    section = "common"
    if site != "common":
        section = consts.SITE_NAMES[site]
    return settings[section][option]


def datadir_required() -> bool:
    checklist = []
    for site in consts.SITES:
        if getoption(site, "enable") is True:
            checklist.append(getoption(site, "login") != "default")
    return any(checklist)


def check_yaml_valid():
    default_section = {"enable": False, "login": "default", "id": None, "password": None}
    edited = False

    default_common = {
        "datadir": None,
        "profile": None,
        "entertoquit": None,
        "waittime": 5,
        "showhotdeal": False,
        "headless": False,
    }

    if "common" not in settings:
        settings["common"] = {}

    for k, v in default_common.items():
        if k not in settings["common"]:
            settings["common"][k] = v
            edited = True

    for site in consts.SITE_NAMES:
        if site not in settings:
            settings[site] = default_section.copy()
            edited = True

    if edited:
        with open(consts.SETTING_FILE_NAME, "w") as f:
            yaml.dump(settings, f, sort_keys=False)
    if datadir_required():
        if settings["common"]["headless"]:
            raise ConfigError("구글/카카오 로그인과 headless 모드를 같이 사용할 수 없습니다.")
        if getoption("common", "datadir") is None or getoption("common", "profile") is None:
            raise ConfigError("구글/카카오 로그인을 사용하려면 설정 파일의 datadir, profile을 지정해 주세요.")

    for site in consts.SITES:
        if getoption(site, "enable") is True:
            login = getoption(site, "login")
            if login == "default" and (getoption(site, "id") is None or getoption(site, "password") is None):
                raise ConfigError(f"설정 파일의 {consts.SITE_NAMES[site]} 아이디와 패스워드를 지정해 주세요.")
            if consts.LOGIN[login][site] is None:
                raise ConfigError(f"{consts.SITE_NAMES[site]}의 {login} 로그인은 지원하지 않습니다.")


def load_settings():
    if len(sys.argv) > 1 and sys.argv[1] == "test":  # test mode
        consts.SETTING_FILE_NAME = "test.yaml"  # noqa

    with open(consts.SETTING_FILE_NAME, "r", encoding="utf-8") as f:  # load yaml
        global settings
        settings = dict(yaml.safe_load(f))

    check_yaml_valid()

    global FILE_LOADED
    FILE_LOADED = True


def entertoquit() -> bool:
    if not FILE_LOADED:
        return True

    if "entertoquit" not in settings["common"]:
        return True
    return getoption("common", "entertoquit")
