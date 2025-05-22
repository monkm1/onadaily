from __future__ import annotations

import asyncio
import itertools
import logging
import sys
from typing import Iterable, Literal, Self

from prettytable import PrettyTable

from config import Site
from consts import DEBUG_MODE
from logsupport import LoggingInfo

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


class WorkingAnimation:
    def __init__(
        self,
        message: str,
        final_message: str,
        error_message: str = "작업 중 오류 발생",
        dynamic_print: bool = True,
        loop_list: list[str] | None = None,
    ) -> None:
        self.message = message
        self.final_message = final_message
        self.error_message = error_message
        self.dynamic_print = dynamic_print

        if DEBUG_MODE:
            self.dynamic_print = False

        if loop_list is None:
            self._loop_list = [".  ", ".. ", "..."]
        else:
            self._loop_list = loop_list

        self.max_pattern_len = max(len(s) for s in self._loop_list)

        self.suffix = itertools.cycle(self._loop_list)

        self._finished_event = asyncio.Event()
        self._anim_task: asyncio.Task | None = None

    async def _show_message_coro(self):
        if not self.dynamic_print:
            print(f"{self.message}{max(self._loop_list)}")
            return
        try:
            while not self._finished_event.is_set():
                current_pattern = next(self.suffix)
                print(f"\r{self.message}{current_pattern}{' ' * self.max_pattern_len}", end="")
                sys.stdout.flush()
                try:
                    await asyncio.wait_for(self._finished_event.wait(), timeout=0.2)
                except asyncio.TimeoutError:
                    pass

        except asyncio.CancelledError:
            pass

    def show_message(self) -> None:
        if not self.dynamic_print:
            print(f"{self.message}{max(self._loop_list)}")
            return
        self._finished_event.clear()
        self._anim_task = asyncio.create_task(self._show_message_coro())

    async def __aenter__(self) -> Self:
        self.show_message()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> Literal[False]:
        if not self.dynamic_print:
            print(self.final_message)
            return False
        await self.stop()
        return False

    async def stop(self, exc_value: Exception | None = None) -> None:
        if not self.dynamic_print:
            print(self.final_message)
            return
        self._finished_event.set()

        if self._anim_task:
            self._anim_task.cancel()
            try:
                await self._anim_task
            except asyncio.CancelledError:
                pass

        clear_len = len(self.message) + self.max_pattern_len + 5

        if exc_value is not None:
            print(f"\r{self.error_message}{' '*clear_len}")
        else:
            print(f"\r{self.final_message}{' '*clear_len}")
