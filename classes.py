from __future__ import annotations

import logging
from typing import Iterable

from prettytable import PrettyTable

from config import Site
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
