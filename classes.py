from __future__ import annotations

import logging
import logging.handlers
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime
from logging import Logger, LogRecord
from typing import Iterable, Literal, Self

from prettytable import PrettyTable

from config import Site
from consts import DEBUG_MODE

logger = logging.getLogger("onadaily.classes")


class HotdealInfo(object):
    name: str
    price: str
    dc_price: str

    def __init__(self, name: str, price: str, dc_price: str) -> None:
        self.name = name.strip()
        price = price.strip()
        dc_price = dc_price.strip()
        if price != "" and price[-1] != "원":
            price += "원"
        if dc_price != "" and dc_price[-1] != "원":
            dc_price += "원"
        self.price = price
        self.dc_price = dc_price

    def to_row(self) -> list[str]:
        return [self.name, self.price, self.dc_price]


class StampResult(object):
    def __init__(self, site: Site) -> None:
        self.site = site
        self.passed = False
        self.iserror = False
        self.resultmessage = ""
        self._logginginfo: LoggingInfo | None = None

    def __bool__(self) -> bool:
        return self.passed

    @property
    def logginginfo(self) -> LoggingInfo:
        if self._logginginfo is None:
            raise ValueError("logginginfo가 초기화되지 않음")
        return self._logginginfo

    @logginginfo.setter
    def logginginfo(self, value: LoggingInfo) -> None:
        self._logginginfo = value


class SaleTable(PrettyTable):
    def __init__(self, site: Site) -> None:
        self.site = site
        super().__init__()
        self.field_names = ["품명", "정상가", "할인가"]

    def keywordcheck(self, keywords) -> list:
        result = []
        for x in self.rows:
            for keyword in keywords:
                if keyword in x[0]:
                    result.append([self.site.name] + x)
        return result

    def add_product(self, product: HotdealInfo) -> None:
        self.add_row(product.to_row())

    def add_products(self, products: Iterable[HotdealInfo]) -> None:
        self.add_rows([product.to_row() for product in products])

    def __len__(self) -> int:
        return len(self.rows)


class LoggingInfo:
    def __init__(
        self,
        exception: Exception | None = None,
        site: Site | None = None,
        version: str = "N/A",
        logcontext: LogCaptureContext | None = None,
    ) -> None:
        self.now = datetime.now()
        self.logcontext = logcontext

        self.iserror = False if exception is None else True
        self.stacktrace = traceback.format_exc() if self.iserror else "N/A"
        self.message = str(exception) if self.iserror else "No error"

        if self.iserror and DEBUG_MODE:
            print(self.stacktrace)

        if site is not None:
            self.sitename = site.name
            self.sitelogin = site.login
        else:
            self.sitename = "None"
            self.sitelogin = "None"

        self.version = "Chrome Version : " + version

        self.saved = False

    @property
    def debuglog(self):
        if self.logcontext is None:
            return "N/A"
        else:
            return self.logcontext.captured_logs_string

    @property
    def printlog(self) -> str:
        if self.logcontext is None:
            return ""
        else:
            return self.logcontext.captured_print_logs_string

    def __str__(self) -> str:
        return (
            f"{self.now}\n\n"
            f"{self.message}\n"
            f"sitename : {self.sitename}\n"
            f"login : {self.sitelogin}\n\n"
            f"{self.stacktrace}\n\n"
            f"====== DEBUG LOG ======\n"
            f"{self.debuglog}\n"
            f"=======================\n\n"
            f"{self.version}"
        )


async_id = ContextVar("async_id", default=None)


class AsyncLogFilter(logging.Filter):
    def __init__(self, capture_id: str) -> None:
        super().__init__()
        self.capture_id = capture_id

    def filter(self, record: LogRecord) -> bool:
        active_id = async_id.get()
        return active_id == self.capture_id


class SiteNameInjector(logging.Filter):
    def __init__(self, site_name: str | None = None) -> None:
        super().__init__()
        self.site_name = site_name if site_name is not None else ""

    def filter(self, record: LogRecord) -> Literal[True]:
        record.site_name = self.site_name
        return True


class LogCaptureContext:
    def __init__(self, logger: Logger, site_name: str) -> None:
        self.logger = logger
        self.site_name = site_name

        self.shared_memory_handler: logging.handlers.MemoryHandler

        self.captured_logs_records: list[LogRecord] = []
        self.captured_logs_string = ""
        self.captured_print_logs_string = ""

        self.formatter = logging.Formatter("%(asctime)s - %(site_name)s:%(module)s - %(message)s")
        self.printformatter = logging.Formatter("%(message)s")

        self.capture_id = str(uuid.uuid4())

    async def __aenter__(self) -> Self:
        logger.debug(f"로그 캡처 시작 id : {self.capture_id}")
        async_id.set(self.capture_id)  # type: ignore[arg-type]
        self.shared_memory_handler = logging.handlers.MemoryHandler(
            capacity=10000, flushLevel=logging.CRITICAL + 1, target=None, flushOnClose=False
        )

        self.shared_memory_handler.addFilter(AsyncLogFilter(self.capture_id))
        self.shared_memory_handler.addFilter(SiteNameInjector(self.site_name))

        self.logger.addHandler(self.shared_memory_handler)

        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> Literal[False]:
        logger.debug("로그 캡처 종료")
        self.logger.removeHandler(self.shared_memory_handler)

        self.captured_logs_records = self.shared_memory_handler.buffer
        self.shared_memory_handler.close()

        logs = [self.formatter.format(record) for record in self.captured_logs_records]
        logs_print = [
            self.printformatter.format(record)
            for record in self.captured_logs_records
            if record.levelno == logging.INFO
        ]

        self.captured_logs_string = "\n".join(logs)
        self.captured_print_logs_string = "\n".join(logs_print)

        return False
