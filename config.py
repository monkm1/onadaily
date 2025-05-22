from __future__ import annotations

import functools
import logging
import shutil
from collections import defaultdict
from os import path
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Optional

import yaml
from attrs import define, field

import consts
from credential_manager import get_credential, set_credential
from errors import ConfigError
from logsupport import add_stream_handler
from utils import asdict_public, check_yaml_types, get_public_field_names

logger = logging.getLogger("onadaily")

if TYPE_CHECKING:  # for mypy
    hidden_field = field
else:

    @functools.wraps(field)
    def hidden_field(**kwargs):
        metadata = kwargs.pop("metadata", {})
        metadata["hidden"] = True
        return field(metadata=metadata, **kwargs)


class Options(object):
    _instance: Optional[Options] = None
    _initialized: bool

    def __new__(cls, *args, **kwargs) -> Options:
        if not cls._instance:
            cls._instance = super(Options, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        logger.debug("Options 초기화")

        self._initialized = True
        self._file_loaded = False

        self._yaml_dict: DefaultDict[str, DefaultDict[str, Any]]
        self.load_settings()

        edited = self._check_update_options()

        self.common = _Common(save_yaml_callback=self.save_yaml, yaml_dict=self._yaml_dict, **self._yaml_dict["common"])

        if not self.common.concurrent and not consts.DEBUG_MODE:
            add_stream_handler(logger, logging.INFO)
        if edited:
            self.save_yaml()

    def _check_update_options(self) -> bool:
        edited = False
        site_fields = Site.public_fields()
        for site_name in consts.SITE_NAMES:
            yaml_fields = set(self._yaml_dict[site_name].keys())

            for site_field in site_fields:
                if site_field not in yaml_fields:  # 파일에 값이 없으므로 기본값 사용
                    edited = True

            for yaml_field in yaml_fields:
                if yaml_field not in site_fields:
                    print(f"알 수 없는 옵션 : {site_name}/{yaml_field}. 삭제합니다.")
                    self._yaml_dict[site_name].pop(yaml_field)
                    edited = True

        common_fields = get_public_field_names(_Common)
        yaml_common_fields = set(self._yaml_dict["common"].keys())

        for common_field in common_fields:
            if common_field not in yaml_common_fields:
                edited = True

        for yaml_field in yaml_common_fields:
            if yaml_field not in common_fields:
                print(f"알 수 없는 옵션 : common/{yaml_field}. 삭제합니다.")
                self._yaml_dict["common"].pop(yaml_field)
                edited = True

        return edited

    def load_settings(self) -> None:
        if not path.isfile(consts.CONFIG_FILE_NAME):
            print("설정 파일이 없습니다. 기본 설정 파일을 복사합니다.")
            shutil.copy(consts.DEFAULT_CONFIG_FILE, consts.CONFIG_FILE_NAME)

        with open(consts.CONFIG_FILE_NAME, "r", encoding="utf-8") as f:  # load yaml
            self._yaml_dict = defaultdict(defaultdict, yaml.safe_load(f))

        self._file_loaded = True

    def save_yaml(self) -> None:
        dump = {}
        dump["common"] = self.common.asdict()

        for site in self.common.order:
            dump[site.name] = site.asdict()

        with open(consts.CONFIG_FILE_NAME, "w", encoding="utf8") as f:
            yaml.dump(dump, f, sort_keys=False, allow_unicode=True)


@define()
class _Common:
    _order: list[str] = hidden_field(
        kw_only=True,
        factory=lambda: ["showdang", "dingdong", "banana", "onami", "domae"],
    )
    _yaml_dict: dict[str, Any] = hidden_field(kw_only=True)
    _save_yaml_callback: Callable[[], None] = hidden_field(kw_only=True)

    entertoquit: bool = field(default=True)
    waittime: int = field(default=10)
    showhotdeal: bool = field(default=False)
    headless: bool = field(default=False)
    order: list[Site] = field(init=False)
    autoretry: bool = field(default=True)
    retrytime: int = field(default=3)
    keywordnoti: list[str] = field(factory=list)
    namespace: str = field(default="Onadaily", converter=str)
    concurrent: bool = field(default=True)

    def __attrs_post_init__(self) -> None:
        self.order = []
        for sitename in self._order:
            self.order.append(
                Site(
                    sitename,
                    namespace=self.namespace,
                    save_yaml_callback=self._save_yaml_callback,
                    **self._yaml_dict[sitename],
                )
            )

        check_yaml_types(self)

    def asdict(self) -> dict[str, Any]:
        return_dict = asdict_public(self)
        return_dict["order"] = self._order

        return return_dict

    @_order.validator
    def _validator_order(self, attr, value):
        error = False
        if not isinstance(value, list):
            error = True
        if len(value) != len(consts.SITE_NAMES):
            error = True
        else:
            for sitename in value:
                if sitename not in consts.SITE_NAMES:
                    error = True

        if error:
            raise ConfigError("설정 파일의 order 항목에 누락되거나 잘못된 사이트가 있습니다.")


@define(eq=False, hash=False, repr=False, str=False)
class Site:
    name: str = hidden_field(repr=False)
    enable: bool = field(default=False)
    login: str = field(default="default")
    credential_storage: str = field(default="keyring")
    _id: Optional[str] = hidden_field(kw_only=True, default=None)
    _password: Optional[str] = hidden_field(kw_only=True, default=None)

    main_url: str = hidden_field(init=False)
    stamp_url: str = hidden_field(init=False)
    login_url: str = hidden_field(init=False)

    input_id: str = hidden_field(init=False)
    input_pwd: str = hidden_field(init=False)
    login_check_xpath: str = hidden_field(init=False)

    btn_stamp: str = hidden_field(init=False)
    hotdeal_table: str | None = hidden_field(init=False)
    stamp_calendar: str = hidden_field(init=False)

    btn_login: str = hidden_field(init=False)

    _save_yaml_callback: Callable[[], None] = hidden_field(kw_only=True)
    _namespace: str = hidden_field(kw_only=True)

    @credential_storage.validator
    def _check_credential_storage(self, attr, value) -> None:
        if value not in ["keyring", "lagacy"]:
            raise ConfigError(f"credential_storage 는 'keyring' 또는 'lagacy'여야 합니다: {value}")

    def __attrs_post_init__(self) -> None:
        self.main_url = consts.URLS[self.name]
        self.stamp_url = consts.STAMP_URLS[self.name]
        self.login_url = consts.LOGIN_URLS[self.name]

        self.input_id = consts.INPUT_ID[self.name]
        self.input_pwd = consts.INPUT_PWD[self.name]
        self.login_check_xpath = consts.CHK_LOGIN[self.name]

        self.btn_stamp = consts.BTN_STAMP[self.name]
        self.hotdeal_table = consts.HOTDEAL_TABLE[self.name]
        self.stamp_calendar = consts.STAMP_CALENDAR[self.name]

        btn_login = consts.LOGIN[self.login][self.name]

        if btn_login is None:
            raise ConfigError(f"'{self.name}' 의 로그인 방식 '{self.login}'은 지원하지 않습니다.")

        self.btn_login = btn_login

        if self.credential_storage == "lagacy":
            print(f"⚠️주의: {self.name}의 'credential_storage'가 'lagacy'로 설정되어 있습니다.")

        check_yaml_types(self)

    def asdict(self) -> dict[str, Any]:
        result = asdict_public(self)
        result["id"] = self._id
        result["password"] = self._password

        return result

    @classmethod
    def public_fields(cls) -> list[str]:
        fields = get_public_field_names(cls)
        fields.extend(["id", "password"])
        return fields

    @property
    def id(self) -> str:
        return self._get_credential("id")

    @property
    def password(self) -> str:
        return self._get_credential("password")

    def _get_credential(self, target: str) -> str:
        if self.login == "default":
            if self.credential_storage == "lagacy":
                return getattr(self, f"_{target}")
            else:
                return self._get_keyring(target)
        else:
            raise ValueError("default가 아닌 로그인 방식은 id, password를 불러오면 안됨")

    def _get_keyring(self, __name: str) -> str:
        if __name in ["id", "password"]:
            name_str_attr = f"_{__name}"
            if self.login != "default":
                raise ValueError("default가 아닌 로그인 방식은 id, password를 불러오면 안됨")

            if getattr(self, name_str_attr) != "saved":  # 저장되지 않은 경우
                credential = set_credential(__name, self.name, self._namespace)
                setattr(self, name_str_attr, "saved")
                self._save_yaml_callback()

            else:
                credential = get_credential(__name, self.name, self._namespace)

            return credential
        else:
            raise ValueError("id/password 속성이 아닌데")

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
