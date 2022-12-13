class ConfigError(Exception):
    pass


class HotdealInfo(object):
    name: str
    price: str
    dc_price: str

    def __init__(self, name, price: str, dc_price):
        self.name = name.strip()
        if price[-1] != "원":
            price += "원"
        if dc_price[-1] != "원":
            dc_price += "원"
        self.price = price
        self.dc_price = dc_price

    def to_row(self):
        return [self.name, self.price, self.dc_price]
