from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from logging import Logger, LogRecord
from typing import Literal, Self

from consts import DEBUG_MODE

logger = logging.getLogger("onadaily.logsupport")

if getattr(sys, "frozen", False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(app_path, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


class LoggingInfo:
    def __init__(
        self,
        exception: Exception | None = None,
        error_traceback: str = "N/A",
        site_name: str = "N/A",
        site_login: str = "N/A",
        version: str = "N/A",
        logcontext: LogCaptureContext | None = None,
    ) -> None:
        self.now = datetime.now()
        self.logcontext = logcontext

        self.iserror = False if exception is None else True
        self.stacktrace = error_traceback
        self.message = str(exception) if self.iserror else "No error"

        if self.iserror and DEBUG_MODE:
            print(self.stacktrace)

        self.sitename = site_name
        self.sitelogin = site_login

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

    def add_message(self, msg: str) -> None:
        if self.logcontext is None:
            return
        else:
            self.logcontext.captured_print_logs_string += f"\n{msg}"
            self.logcontext.captured_logs_string += f"\n{msg}"

    def __str__(self) -> str:
        return (
            f"{self.now}\n\n"
            f"{self.message}\n"
            f"sitename : {self.sitename}\n"
            f"login : {self.sitelogin}\n\n"
            f"====== STACKTRACE ======\n"
            f"{self.stacktrace}\n\n"
            f"====== DEBUG LOG ======\n"
            f"{self.debuglog}\n"
            f"=======================\n\n"
            f"{self.version}"
        )


async_id = ContextVar[str | None]("async_id", default=None)


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
        async_id.set(self.capture_id)
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


def save_log(logginginfo: LoggingInfo) -> str:
    if logginginfo.saved:
        logger.debug("이미 저장된 로그")
        return ""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        prefix = "error" if logginginfo.iserror else "log"

        filename = os.path.join(LOG_DIR, f"{prefix}_{logginginfo.sitename}_{timestamp}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(logginginfo))

    except Exception as ex:
        print(f"로깅 실패 : {ex}")
        print(f"원본 오류 : \n{logginginfo.stacktrace}")

    logginginfo.saved = True
    print(f"로그 저장됨: {filename}")
    return filename


def add_stream_handler(logger: logging.Logger, level: int = logging.DEBUG, include_module_name: bool = False) -> None:
    handler = logging.StreamHandler()
    handler.setLevel(level)
    module_name = "%(module)s - " if include_module_name else ""
    formatter = logging.Formatter(f"{module_name}%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
