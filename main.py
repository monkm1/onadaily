import logging

from yaml import YAMLError

from config import Options
from consts import DEBUG_MODE
from errors import ConfigError
from onadaily import Onadaily

if __name__ == "__main__":
    options = None
    try:
        logger = logging.getLogger("onadaily")
        logger.setLevel(logging.DEBUG)

        if DEBUG_MODE:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(module)s - %(message)s")
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
        if options is None or options.common.entertoquit:
            input("종료하려면 Enter를 누르세요...")
