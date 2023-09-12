import prettytable

from config import Site


class SaleTable(prettytable.PrettyTable):
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
