import abc
import logging
from typing import Iterable

from bs4 import BeautifulSoup, Tag

from classes import HotdealInfo, SaleTable
from config import Site
from errors import HotDealDataNotFoundError, HotDealTableParseError

logger = logging.getLogger("onadaily")


class BaseHotDealStrategy(abc.ABC):
    def get_hotdeal_info(self, page_source: str, site: Site) -> SaleTable:
        soup = self._get_soup(page_source)

        table = self._get_hotdeal_table(soup, site)

        products = self._get_product_list(table)

        hotdeallist = self._foreach_products(products)

        resulttable = SaleTable(site)
        resulttable.add_products(hotdeallist)
        return resulttable

    def _get_soup(self, page_source: str) -> BeautifulSoup:
        return BeautifulSoup(page_source, "html.parser")

    def _get_hotdeal_table(self, soup: BeautifulSoup, site: Site) -> Tag:
        if site.hotdeal_table is None:
            raise HotDealTableParseError("잘못된 사이트 설정")
        table = soup.select_one(site.hotdeal_table)

        if table is None:
            raise HotDealDataNotFoundError("핫딜 테이블 찾을 수 없음")

        return table

    def _get_product_list(self, table: Tag) -> Iterable[Tag]:
        if (div := table.select_one("div")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")

        products = div.find_all("div", recursive=False)

        if len(products) == 0:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")

        result = [
            list(x.children)[1]
            for x in products
            if x.has_attr("data-swiper-slide-index") and "swiper-slide-duplicate" not in x["class"]
        ]
        return result

    def _foreach_products(self, products: Iterable[Tag]) -> list[HotdealInfo]:
        hotdealinfolist = []
        for product in products:
            try:
                info = self._get_product_info(product)
            except HotDealDataNotFoundError:
                logger.debug("핫딜 파싱 중 상품이 없음")
                continue

            hotdealinfolist.append(info)

        return hotdealinfolist

    @abc.abstractmethod
    def _get_product_info(self, product: Tag) -> HotdealInfo:
        pass


class OnamiHotDealStrategy(BaseHotDealStrategy):
    def _get_product_info(self, product: Tag) -> HotdealInfo:
        price = dc_price = name = "이게 보이면 오류"

        if (dcpricespan := product.select_one("p.price > span")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")
        dc_price = dcpricespan.text

        if (pricestrike := product.select_one("strike")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")

        price = pricestrike.text

        if (namep := product.select_one("p.name")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")

        name = namep.text

        return HotdealInfo(name, price, dc_price)


class ShowDangHotDealStrategy(BaseHotDealStrategy):
    def _get_product_info(self, product: Tag) -> HotdealInfo:
        price = dc_price = name = "이게 보이면 오류"

        if (price_span := product.select_one("span.or-price")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")
        price = price_span.text

        if (dc_price_span := product.select_one("span.sl-price")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")
        dc_price = dc_price_span.text

        if (name_ul := product.select_one("ul.swiper-prd-info-name")) is None:
            raise HotDealDataNotFoundError("핫딜 테이블에 상품이 없음")
        name = name_ul.text

        return HotdealInfo(name, price, dc_price)


def get_hotdeal_strategy(site: Site) -> BaseHotDealStrategy:
    if site.name == "onami":
        return OnamiHotDealStrategy()
    elif site.name == "showdang":
        return ShowDangHotDealStrategy()
    else:
        raise HotDealTableParseError(f"{site.name} 핫딜 테이블 파싱 지원 안됨")
