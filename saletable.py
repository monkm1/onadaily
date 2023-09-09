import prettytable

from config import Site


class SaleTable(prettytable.PrettyTable):
    def __init__(self, site: Site):
        self.site = site
        super().__init__()

    def keywordcheck(self, keywords):
        result = []
        for x in self.rows:
            for keyword in keywords:
                if keyword in x[0]:
                    result.append([self.site.name] + x)
        return result
