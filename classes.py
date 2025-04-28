from prettytable import PrettyTable

from config import Site


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

    def keywordcheck(self, keywords) -> list:
        result = []
        for x in self.rows:
            for keyword in keywords:
                if keyword in x[0]:
                    result.append([self.site.name] + x)
        return result

    def __len__(self) -> int:
        return len(self.rows)
