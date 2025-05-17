import logging
import shutil
from os import path
from typing import Any, Dict, Optional, get_type_hints

import yaml

import consts
from credential_manager import get_credential, set_credential
from errors import ConfigError

logger = logging.getLogger("onadaily")


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

        self._settings: Dict[str, Dict[str, Any]] = {}
        self.load_settings()

        self.sites = [Site(site_name, self) for site_name in consts.SITE_NAMES]
        self.common = _Common(self)  # common에서 self.sites를 참조하기 때문에 self.sites를 먼저 초기화해야 함

    def _getoption(self, section: str, option: str) -> Any:
        if section not in self._settings:
            raise ValueError("잘못된 옵션 접근")

        return self._settings[section][option]

    def load_settings(self) -> None:
        if not path.isfile(consts.CONFIG_FILE_NAME):
            print("설정 파일이 없습니다. 기본 설정 파일을 복사합니다.")
            shutil.copy(consts.DEFAULT_CONFIG_FILE, consts.CONFIG_FILE_NAME)

        with open(consts.CONFIG_FILE_NAME, "r", encoding="utf-8") as f:  # load yaml
            self._settings = dict(yaml.safe_load(f))

        self._check_yaml_valid()

        self._file_loaded = True

        if self._settings["common"]["credential_storage"] == "lagacy":
            print("⚠️주의: credential_storage가 lagacy로 설정되어 있습니다.")
            print("아이디/비밀번호를 파일에 저장합니다. 보안에 주의하세요.")
            print("암호화된 저장소에 저장하려면 credential_storage를 keyring으로 변경하세요.")

    def datadir_required(self) -> bool:
        checklist = []
        for sitename, sitesettings in self._settings.items():
            if sitename == "common":
                continue

            if sitesettings["enable"] is True:
                checklist.append(sitesettings["login"] != "default")
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
            "credential_storage": "keyring",
            "namespace": "Onadaily",
        }

        common_type_hint = get_type_hints(_Common)

        if len(common_type_hint) + 1 != len(default_common):
            raise ValueError("타입 힌트 수정해야 함")

        if "common" not in self._settings:  # common 섹션이 없으면 추가
            self._settings["common"] = {}

        for k, v in default_common.items():  # 기본 common 섹션에서 없는 항목 추가
            if k not in self._settings["common"]:
                self._settings["common"][k] = v

        for sitename in consts.SITE_NAMES:
            if sitename not in self._settings:  # 사이트 섹션이 없으면 추가
                self._settings[sitename] = default_section.copy()  # 얕은 복사
                self._settings["common"]["order"].append(sitename)  # 사이트 섹션 추가 시 order에 추가

        # if self.datadir_required():
        # if self._settings["common"]["headless"]:
        # raise ConfigError("소셜 로그인과 headless 모드를 같이 사용할 수 없습니다.")

        if self._settings["common"]["credential_storage"] not in ["keyring", "lagacy"]:
            print("잘못된 credential_storage 설정, 기본값 keyring으로 설정합니다.")
            self._settings["common"]["credential_storage"] = "keyring"

        for sitename, sitesettings in self._settings.items():
            if sitename == "common":
                continue

            if sitesettings["enable"] is True:
                login = sitesettings["login"]
                if consts.LOGIN[login][sitename] is None:
                    raise ConfigError(f"{sitename}의 {login} 로그인은 지원하지 않습니다.")

        order = self._settings["common"]["order"]

        if len(set(order)) != len(consts.SITE_NAMES):
            raise ConfigError("설정 파일의 order 항목에 중복되거나 누락된 사이트가 있습니다.")

        for s in order:
            if s not in consts.SITE_NAMES:
                raise ConfigError("설정 파일의 order 항목에 사이트 철자가 틀렸습니다.")

        self.save_yaml()

    def save_yaml(self) -> None:
        with open(consts.CONFIG_FILE_NAME, "w", encoding="utf8") as f:
            yaml.dump(self._settings, f, sort_keys=False, allow_unicode=True)


class _Common(object):
    entertoquit: bool
    waittime: int
    showhotdeal: bool
    headless: bool
    autoretry: bool
    retrytime: int
    keywordnoti: list[str]
    credential_storage: str
    namespace: str

    def __init__(self, options: Options) -> None:
        self._order: list["Site"] = []
        self._options = options
        for ordername in options._settings["common"]["order"]:
            for site in options.sites:
                if site.name == ordername:
                    self._order.append(site)

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

    @property
    def btn_login(self) -> str | None:
        return consts.LOGIN[self.login][self.name]

    def __getattr__(self, __name: str) -> Any:
        if __name in ["id", "password"]:
            if self.login != "default":
                raise ValueError("default가 아닌 로그인 방식은 id, password를 불러오면 안됨")

            if self._options.common.credential_storage == "lagacy":
                return self._options._getoption(self.name, __name)
            else:
                if self._options._getoption(self.name, __name) != "saved":  # 저장되지 않은 경우
                    credential = set_credential(__name, self.name, self._options.common.namespace)
                    self.save_credential_status(__name)

                else:
                    credential = get_credential(__name, self.name, self._options.common.namespace)

                return credential
        else:
            return self._options._getoption(self.name, __name)

    def save_credential_status(self, type: str) -> None:
        self._options._settings[self.name][type] = "saved"
        self._options.save_yaml()

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

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name
