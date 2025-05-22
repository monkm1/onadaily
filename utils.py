from __future__ import annotations

import functools
import logging
from datetime import datetime
from math import ceil
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    ParamSpec,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import pytz
from attrs import Attribute, AttrsInstance, asdict, fields
from bs4 import BeautifulSoup
from patchright import async_api
from patchright.async_api import TimeoutError

from errors import ConfigError

logger = logging.getLogger("onadaily")


def check_already_stamp(sitename: str, source: str) -> bool:
    soup = BeautifulSoup(source, "html.parser")

    week, day = num_of_month_week()

    logger.debug(f"주차 : {week}, 요일 : {day}")

    weekssoup = soup.find_all(True, recursive=False)
    weeksoup = weekssoup[week - 1].find_all(True, recursive=False)

    todaysoup = weeksoup[day - 1]

    if sitename != "banana":
        if todaysoup.find("img", {"alt": "출석"}) is None:
            return False
        else:
            return True
    else:
        if todaysoup.find("img") is None:
            return False
        else:
            return True


def num_of_month_week() -> tuple[int, int]:
    date = datetime.now(pytz.timezone("Asia/Seoul"))
    first_day = date.replace(day=1)

    day_of_month = date.day

    if first_day.weekday() == 6:
        adjusted_dom = day_of_month + 1
    else:
        adjusted_dom = day_of_month + first_day.weekday() + 1

    weeknum = int(ceil(adjusted_dom / 7.0))
    dayofweeknum = (date.weekday() + 1) % 7 + 1

    return weeknum, dayofweeknum


R = TypeVar("R")
P = ParamSpec("P")


class HandlePlayWrightError:
    def __init__(self, wrap_exception: Type[Exception], message_prefix: str) -> None:
        self.wrap_exception = wrap_exception
        self.message_prefix = message_prefix

    def __call__(self, func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await func(*args, **kwargs)
            except TimeoutError as ex:
                raise self.wrap_exception(f"{self.message_prefix}/시간 초과") from ex
            except async_api.Error as ex:
                raise self.wrap_exception(f"{self.message_prefix}/플레이라이트 에러") from ex
            except Exception as ex:
                raise self.wrap_exception(f"{self.message_prefix}/알 수 없는 에러") from ex

        return wrapper


def filter_attr(attr: Attribute, value: Any) -> bool:
    return not attr.metadata.get("hidden", False)


def asdict_public(instance: AttrsInstance) -> dict[str, Any]:
    return asdict(instance, filter=filter_attr)


def get_public_field_names(class_: type[AttrsInstance]) -> list[str]:
    class_fields = fields(class_)
    result = []

    for field in class_fields:
        if field.metadata.get("hidden", False):
            continue
        result.append(field.name)

    return result


def isinstance_of_simple_type_hint(value: Any, type_hint: Any) -> bool:
    origin = get_origin(type_hint)
    args = get_args(type_hint)

    if origin is not None:
        if origin is Union:
            if value is None and type(None) in args:
                return True
            return any(isinstance_of_simple_type_hint(value, arg) for arg in args if arg is not type(None))
        elif origin is list or origin is List:
            return isinstance(value, list)
        elif origin is dict or origin is Dict:
            return isinstance(value, dict)
        elif origin is tuple or origin is Tuple:
            return isinstance(value, tuple)
        elif origin is Callable:
            return callable(value)
        else:
            try:
                return isinstance(value, origin)
            except TypeError:
                return True
    else:
        if type_hint is Any:
            return True
        if type_hint is type(None) and value is None:
            return True
        return isinstance(value, type_hint)


def check_yaml_types(instance: AttrsInstance):
    typehints = get_type_hints(instance.__class__)
    public_fields = get_public_field_names(instance.__class__)
    for attr in fields(instance.__class__):
        if attr.name not in public_fields:
            continue

        value = getattr(instance, attr.name)

        if attr.name in typehints:
            expected_type = typehints[attr.name]

            if not isinstance_of_simple_type_hint(value, expected_type):
                name = getattr(instance, "name", "common")
                raise ConfigError(f"잘못된 옵션 / [{name}] 옵션: {attr.name}, 값: {value}")
