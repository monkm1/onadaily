import shutil
import sys
from os import path
from typing import Any, Dict, Optional, get_type_hints

import yaml

import consts
from classes import ConfigError

_FILE_LOADED = False
_settings: Dict[str, Any] = {}


def _getoption(sitename: str, option: str):
    section = "common"
    if sitename != "common":
        section = sitename
    return _settings[section][option]


class _Options(object):
    def __init__(self) -> None:
        self.common = _Common()
        self.sites: list[Site] = []

        for sitecode in consts.SITES:
            self.sites.append(Site(sitecode))

    def load_settings(self):
        if len(sys.argv) > 1 and sys.argv[1] == "test":  # test mode
            consts.SETTING_FILE_NAME = "test.yaml"  # noqa

        if not path.isfile(consts.SETTING_FILE_NAME):
            shutil.copy("onadailyorigin.yaml", consts.SETTING_FILE_NAME)

        with open(consts.SETTING_FILE_NAME, "r", encoding="utf-8") as f:  # load yaml
            global _settings
            _settings = dict(yaml.safe_load(f))

        self._check_yaml_valid()

        global _FILE_LOADED
        _FILE_LOADED = True

        order = _getoption("common", "order")
        self.common._order = []
        for sitename in order:
            self.common._order.append(self.getsite(sitename))

    def getsite(self, sitename) -> "Site":
        return [x for x in self.sites if x.name == sitename][0]

    def datadir_required(self) -> bool:
        checklist = []
        for site in self.sites:
            if site.enable is True:
                checklist.append(site.login != "default")
        return any(checklist)

    def _check_yaml_valid(self):
        default_section = {"enable": False, "login": "default", "id": None, "password": None}
        edited = False

        default_common = {
            "datadir": None,
            "profile": None,
            "entertoquit": True,
            "waittime": 5,
            "showhotdeal": False,
            "headless": False,
            "order": ["showdang", "dingdong", "banana", "onami", "domae"],
            "autoretry": True,
            "retrytime": 3,
            "keywordnoti": [],
        }

        common_type_hint = get_type_hints(_Common)

        if len(common_type_hint) + 1 != len(default_common):
            raise ValueError("타입 힌트 수정해야 함")

        if "common" not in _settings:
            _settings["common"] = {}

        for k, v in default_common.items():
            if k not in _settings["common"]:
                _settings["common"][k] = v
                edited = True

        for site in consts.SITE_NAMES:
            if site not in _settings:
                _settings[site] = default_section.copy()
                _settings["common"]["order"].append(site)
                edited = True

        if edited:
            with open(consts.SETTING_FILE_NAME, "w") as f:
                yaml.dump(_settings, f, sort_keys=False)
        if self.datadir_required():
            if _settings["common"]["headless"]:
                raise ConfigError("소셜 로그인과 headless 모드를 같이 사용할 수 없습니다.")
            if _getoption("common", "datadir") is None or _getoption("common", "profile") is None:
                raise ConfigError("소셜 로그인을 사용하려면 설정 파일의 datadir, profile을 지정해 주세요.")

        for site in self.sites:
            if site.enable is True:
                login = site.login
                if login == "default" and (site.id is None or site.password is None):
                    raise ConfigError(f"설정 파일의 {site.name} 아이디와 패스워드를 지정해 주세요.")
                if site.btn_login is None:
                    raise ConfigError(f"{site.name}의 {login} 로그인은 지원하지 않습니다.")

        order = _settings["common"]["order"]

        if len(set(order)) != len(consts.SITES):
            raise ConfigError("설정 파일의 order 항목에 중복되거나 누락된 사이트가 있습니다.")

        for s in order:
            if s not in consts.SITE_NAMES:
                raise ConfigError("설정 파일의 order 항목에 사이트 철자가 틀렸습니다.")

    def __getattr__(self, __name: str) -> Any:
        if not _FILE_LOADED:
            raise ConfigError("설정 파일이 로드되지 않음")
        super().__getattribute__(__name)


class _Common(object):
    datadir: Optional[str]
    profile: Optional[str]
    entertoquit: bool
    waittime: int
    showhotdeal: bool
    headless: bool
    autoretry: bool
    retrytime: int
    keywordnoti: list[str]

    def __init__(self) -> None:
        self._order: Optional[list["Site"]] = None

    def __getattr__(self, key):
        if key == "entertoquit":
            return self._entertoquit()
        return _getoption("common", key)

    @property
    def order(self) -> list["Site"]:
        if self._order is None:
            raise ValueError()
        return self._order

    def _entertoquit(self) -> bool:
        if not _FILE_LOADED:
            return True

        if "entertoquit" not in _settings["common"]:
            return True
        return _getoption("common", "entertoquit")


class Site(object):
    name: str
    enable: bool
    login: str
    id: Optional[str]
    password: Optional[str]

    def __init__(self, sitecode: int) -> None:
        self.code = sitecode
        self.name = consts.SITE_NAMES[sitecode]
        self.main_url = consts.URLS[sitecode]
        self.stamp_url = consts.STAMP_URLS[sitecode]
        self.login_url = consts.LOGIN_URLS[sitecode]

        self.input_id = consts.INPUT_ID[sitecode]
        self.input_pwd = consts.INPUT_PWD[sitecode]
        self.login_check_xpath = consts.CHK_LOGIN[sitecode]

        self.btn_stamp = consts.BTN_STAMP[sitecode]
        self.hotdeal_table = consts.HOTDEAL_TABLE[sitecode]  # type: ignore
        self.stamp_calendar = consts.STAMP_CALENDAR[sitecode]

    @property
    def btn_login(self) -> str:
        return consts.LOGIN[self.login][self.code]

    def __getattr__(self, __name: str) -> Any:
        return _getoption(self.name, __name)

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Site):
            return False

        if __value.id == self.id and __value.name == self.name:
            return True
        else:
            return False

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __hash__(self):
        return hash(self.name)


options = _Options()
