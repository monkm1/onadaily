import functools
import logging
import os
import sys
from datetime import datetime
from math import ceil
from typing import Any, Callable, Type, TypeVar, cast

import pytz
from bs4 import BeautifulSoup
from patchright.async_api import TimeoutError

from classes import LoggingInfo
from config import Site

logger = logging.getLogger("onadaily")


def check_already_stamp(site: Site, source: str) -> bool:
    soup = BeautifulSoup(source, "html.parser")

    week, day = num_of_month_week()

    logger.debug(f"주차 : {week}, 요일 : {day}")

    weekssoup = soup.find_all(True, recursive=False)
    weeksoup = weekssoup[week - 1].find_all(True, recursive=False)

    todaysoup = weeksoup[day - 1]

    if site.name != "banana":
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


if getattr(sys, "frozen", False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(app_path, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def save_log_error(logginginfo: LoggingInfo) -> str:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.join(LOG_DIR, f"error_{logginginfo.sitename}_{timestamp}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(logginginfo))

    except Exception as ex:
        print(f"로깅 실패 : {ex}")
        print(f"원본 오류 : \n{logginginfo.stacktrace}")

    return filename


T = TypeVar("T", bound=Callable[..., Any])


class HandlePlayWrightError:
    def __init__(self, wrap_exception: Type[Exception], message_prefix: str) -> None:
        self.wrap_exception = wrap_exception
        self.message_prefix = message_prefix

    def __call__(self, func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TimeoutError as ex:
                raise self.wrap_exception(f"{self.message_prefix}/시간 초과") from ex
            except Exception as ex:
                raise self.wrap_exception(f"{self.message_prefix}/알 수 없는 에러") from ex

        return cast(T, wrapper)
