import logging
import logging.handlers
import traceback
from datetime import datetime
from logging import Logger, LogRecord
from typing import Iterable, Literal, Self

from prettytable import PrettyTable

from config import Site
from consts import DEBUG_MODE
from webdriverwrapper import WebDriverWrapper

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
        self.message = ""

    def __bool__(self) -> bool:
        return self.passed


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
        exception: Exception,
        site: Site | None = None,
        driver: WebDriverWrapper | None = None,
        debuglog: str | None = None,
    ) -> None:
        self.now = datetime.now()
        self.stacktrace = traceback.format_exc()

        if DEBUG_MODE:
            print(self.stacktrace)

        self.message = str(exception)

        if site is not None:
            self.sitename = site.name
            self.sitelogin = site.login
        else:
            self.sitename = "None"
            self.sitelogin = "None"

        if driver is not None and not driver.quited:
            try:
                self.version = f"Chrome version : {driver.capabilities['browserVersion']}"
            except:  # noqa
                self.version = "Chrome version : N/A"
        else:
            self.version = "Chrome version : N/A"

        if debuglog is not None:
            self.debuglog = debuglog
        else:
            self.debuglog = "N/A"

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


class LogCaptureContext:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.shared_memory_handler: logging.handlers.MemoryHandler

        self.captured_logs_records: list[LogRecord] = []
        self.captured_logs_string = ""

        self.formatter = logging.Formatter("%(asctime)s - %(module)s - %(message)s")

    def __enter__(self) -> Self:
        logger.debug("로그 캡처 시작")
        self.shared_memory_handler = logging.handlers.MemoryHandler(
            capacity=10000, flushLevel=logging.CRITICAL + 1, target=None, flushOnClose=False
        )

        self.logger.addHandler(self.shared_memory_handler)

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> Literal[False]:
        logger.debug("로그 캡처 종료")
        self.logger.removeHandler(self.shared_memory_handler)

        self.captured_logs_records = self.shared_memory_handler.buffer
        self.shared_memory_handler.close()

        logs = [self.formatter.format(record) for record in self.captured_logs_records]

        self.captured_logs_string = "\n".join(logs)

        return False
