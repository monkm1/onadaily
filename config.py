import shutil
import sys
from os import path
from typing import Any, Dict, Optional, get_type_hints

import yaml

import consts
from classes import ConfigError


class _Options(object):
    def __init__(self) -> None:
        self.common = _Common(self)
        self.sites = [Site(sitecode, self) for sitecode in consts.SITES]
        self._settings: Dict[str, Dict[str, Any]] = {}
        self._file_loaded = False

    def _getoption(self, sitename: str, option: str) -> Any:
        section = "common"
        if sitename != "common":
            section = sitename

        if section not in self._settings:
            raise ValueError("잘못된 옵션 접근")

        return self._settings[section][option]

    def load_settings(self) -> None:
        if len(sys.argv) > 1 and sys.argv[1] == "test":  # test mode
            consts.SETTING_FILE_NAME = "test.yaml"  # noqa

        if not path.isfile(consts.SETTING_FILE_NAME):
            shutil.copy("onadailyorigin.yaml", consts.SETTING_FILE_NAME)

        with open(consts.SETTING_FILE_NAME, "r", encoding="utf-8") as f:  # load yaml
            self._settings = dict(yaml.safe_load(f))

        self._check_yaml_valid()

        self._file_loaded = True

        order = self._getoption("common", "order")
        self.common._order = []
        for sitename in order:
            self.common._order.append(self.getsite(sitename))

    def getsite(self, sitename: str) -> "Site":
        return [x for x in self.sites if x.name == sitename][0]

    def datadir_required(self) -> bool:
        checklist = []
        for site in self.sites:
            if site.enable is True:
                checklist.append(site.login != "default")
        return any(checklist)

    def _check_yaml_valid(self) -> None:
        default_section = {"enable": False, "login": "default", "id": None, "password": None}

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

        if "common" not in self._settings:
            self._settings["common"] = {}

        for k, v in default_common.items():
            if k not in self._settings["common"]:
                self._settings["common"][k] = v

        for sitename in consts.SITE_NAMES:
            if sitename not in self._settings:
                self._settings[sitename] = default_section.copy()
                self._settings["common"]["order"].append(sitename)

        with open(consts.SETTING_FILE_NAME, "w", encoding="utf8") as f:
            yaml.dump(self._settings, f, sort_keys=False, allow_unicode=True)

        if self.datadir_required():
            if self._settings["common"]["headless"]:
                raise ConfigError("소셜 로그인과 headless 모드를 같이 사용할 수 없습니다.")
            if self._getoption("common", "datadir") is None or self._getoption("common", "profile") is None:
                raise ConfigError("소셜 로그인을 사용하려면 설정 파일의 datadir, profile을 지정해 주세요.")

        for site in self.sites:
            if site.enable is True:
                login = site.login
                if login == "default" and (site.id is None or site.password is None):
                    raise ConfigError(f"설정 파일의 {site.name} 아이디와 패스워드를 지정해 주세요.")
                if site.btn_login is None:
                    raise ConfigError(f"{site.name}의 {login} 로그인은 지원하지 않습니다.")

        order = self._settings["common"]["order"]

        if len(set(order)) != len(consts.SITES):
            raise ConfigError("설정 파일의 order 항목에 중복되거나 누락된 사이트가 있습니다.")

        for s in order:
            if s not in consts.SITE_NAMES:
                raise ConfigError("설정 파일의 order 항목에 사이트 철자가 틀렸습니다.")

    def __getattr__(self, __name: str) -> Any:
        if not self._file_loaded:
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

    def __init__(self, options: _Options) -> None:
        self._order: Optional[list["Site"]] = None
        self._options = options

    def __getattr__(self, key: str) -> Any:
        if key == "entertoquit":
            return self._entertoquit()
        return self._options._getoption("common", key)

    @property
    def order(self) -> list["Site"]:
        if self._order is None:
            raise ValueError()
        return self._order

    def _entertoquit(self) -> bool:
        if not self._options._file_loaded:
            return True

        if "entertoquit" not in self._options._settings["common"]:
            return True
        return self._options._getoption("common", "entertoquit")


class Site(object):
    name: str
    enable: bool
    login: str
    id: Optional[str]
    password: Optional[str]

    def __init__(self, sitecode: int, options: _Options) -> None:
        self._options = options

        self.code = sitecode
        self.name = consts.SITE_NAMES[sitecode]
        self.main_url = consts.URLS[self.name]
        self.stamp_url = consts.STAMP_URLS[self.name]
        self.login_url = consts.LOGIN_URLS[self.name]

        self.input_id = consts.INPUT_ID[self.name]
        self.input_pwd = consts.INPUT_PWD[self.name]
        self.login_check_xpath = consts.CHK_LOGIN[self.name]

        self.btn_stamp = consts.BTN_STAMP[self.name]
        self.hotdeal_table = consts.HOTDEAL_TABLE[self.name]
        self.stamp_calendar = consts.STAMP_CALENDAR[self.name]

    @property
    def btn_login(self) -> str | None:
        return consts.LOGIN[self.login][self.name]

    def __getattr__(self, __name: str) -> Any:
        return self._options._getoption(self.name, __name)

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Site):
            return False

        if __value.id == self.id and __value.name == self.name:
            return True
        else:
            return False

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __hash__(self) -> int:
        return hash(self.name)


options = _Options()
