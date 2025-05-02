import logging

from yaml import YAMLError

from config import Options
from consts import DEBUG_MODE
from errors import ConfigError
from onadaily import Onadaily

if __name__ == "__main__":

    try:
        logger = logging.getLogger("onadaily")
        if DEBUG_MODE:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        options = Options()

        main = Onadaily()
        main.run()
    except ConfigError as e:
        logger.exception(f"설정 파일 오류 : {e}\n")
    except YAMLError as e:
        logger.exception(f"설정 파일 분석 중 오류 발생 : {e}\n")
    except Exception as e:
        logger.exception(f"예상치 못한 오류 발생 : {e}\n")

    finally:
        if options is not None and options.common.entertoquit:
            input("종료하려면 Enter를 누르세요...")
