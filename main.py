import logging

from yaml import YAMLError

from classes import ConfigError
from config import options
from onadaily import Onadaily

if __name__ == "__main__":

    logger = logging.getLogger("onadaily")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    try:
        main = Onadaily()
        main.run()
    except ConfigError as ex:
        logger.exception("설정 파일 오류 :\n", ex)
    except YAMLError:
        logger.exception("설정 파일 분석 중 오류 발생 :")

    if options.common.entertoquit:
        input("종료하려면 Enter를 누르세요...")
