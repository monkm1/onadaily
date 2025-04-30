import logging
import shutil
import sys
from os import path
from typing import Any, Dict, Optional, get_type_hints

import keyring
import pwinput  # type: ignore[import-untyped]
import yaml
from keyring.errors import PasswordDeleteError

import consts
from errors import ConfigError

logger = logging.getLogger("onadaily")
DEBUG_MODE = False

if len(sys.argv) > 1 and sys.argv[1] == "test":
    DEBUG_MODE = True


class Options(object):
    _instance: Optional["Options"] = None
    _initialized: bool

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Options, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        logger.debug("Options 초기화")

        self._initialized = True
        self._file_loaded = False

        self.common = _Common(self)
        self.sites = [Site(site_name, self) for site_name in consts.SITE_NAMES]
        self._settings: Dict[str, Dict[str, Any]] = {}

        self.load_settings()

    def _getoption(self, sitename: str, option: str) -> Any:
        section = "common"
        if sitename != "common":
            section = sitename

        if section not in self._settings:
            raise ValueError("잘못된 옵션 접근")

        return self._settings[section][option]

    def load_settings(self) -> None:
        if DEBUG_MODE:  # test mode
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
                self._settings[sitename] = default_section.copy()  # 얕은 복사
                self._settings["common"]["order"].append(sitename)

        if self.datadir_required():
            if self._settings["common"]["headless"]:
                raise ConfigError("소셜 로그인과 headless 모드를 같이 사용할 수 없습니다.")

        for site in self.sites:
            if site.enable is True:
                login = site.login
                if site.btn_login is None:
                    raise ConfigError(f"{site.name}의 {login} 로그인은 지원하지 않습니다.")

        order = self._settings["common"]["order"]

        if len(set(order)) != len(consts.SITES):
            raise ConfigError("설정 파일의 order 항목에 중복되거나 누락된 사이트가 있습니다.")

        for s in order:
            if s not in consts.SITE_NAMES:
                raise ConfigError("설정 파일의 order 항목에 사이트 철자가 틀렸습니다.")

        self.save_yaml()

    def save_yaml(self) -> None:
        with open(consts.SETTING_FILE_NAME, "w", encoding="utf8") as f:
            yaml.dump(self._settings, f, sort_keys=False, allow_unicode=True)


class _Common(object):
    entertoquit: bool
    waittime: int
    showhotdeal: bool
    headless: bool
    autoretry: bool
    retrytime: int
    keywordnoti: list[str]

    def __init__(self, options: Options) -> None:
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

    def __init__(self, sitename: str, options: Options) -> None:
        self._options = options

        self.name = sitename
        self.main_url = consts.URLS[self.name]
        self.stamp_url = consts.STAMP_URLS[self.name]
        self.login_url = consts.LOGIN_URLS[self.name]

        self.input_id = consts.INPUT_ID[self.name]
        self.input_pwd = consts.INPUT_PWD[self.name]
        self.login_check_xpath = consts.CHK_LOGIN[self.name]

        self.btn_stamp = consts.BTN_STAMP[self.name]
        self.hotdeal_table = consts.HOTDEAL_TABLE[self.name]
        self.stamp_calendar = consts.STAMP_CALENDAR[self.name]

        self._serviceName = "Onadaily"

    @property
    def btn_login(self) -> str | None:
        return consts.LOGIN[self.login][self.name]

    def __getattr__(self, __name: str) -> Any:
        if __name == "id":
            if self._options._getoption(self.name, "id") != "saved" or self.get_credential("id") is None:
                while True:
                    id = input(f"{self.name} 의 아이디 입력 :")

                    if not id or id.isspace():
                        print("🚨 아이디를 입력해 주세요.")
                        continue

                    self.save_credential("id", id)
                    print("✅ 아이디 저장 완료!")
                    break

            return self.get_credential("id")

        elif __name == "password":
            if self._options._getoption(self.name, "password") != "saved" or self.get_credential("password") is None:
                while True:
                    password1 = pwinput.pwinput(prompt=f"{self.name}의 비밀번호 입력 :")

                    if not password1 or password1.isspace():
                        print("🚨 패스워드를 입력해 주세요.")
                        continue

                    password2 = pwinput.pwinput(prompt="다시 입력 :")

                    if password1 == password2:
                        self.save_credential("password", password1)
                        print("✅ 비밀번호 확인 및 저장 완료!")
                        break
                    else:
                        print("🚨 비밀번호가 일치하지 않습니다. 다시 입력해주세요.")

            return self.get_credential("password")

        return self._options._getoption(self.name, __name)

    def save_credential(self, type: str, value: str) -> None:
        if type not in ["id", "password"]:
            raise ValueError("잘못된 type")

        try:
            keyring.delete_password(f"{self._serviceName}@{self.name}", type)
        except PasswordDeleteError:
            pass

        keyring.set_password(f"{self._serviceName}@{self.name}", type, value)

        self._options._settings[self.name][type] = "saved"
        self._options.save_yaml()

    def get_credential(self, type: str) -> str | None:
        if type not in ["id", "password"]:
            raise ValueError("잘못된 type")
        return keyring.get_password(f"{self._serviceName}@{self.name}", type)

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Site):
            return NotImplemented

        if __value.name == self.name:
            return True
        else:
            return False

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self):
        return self.name
