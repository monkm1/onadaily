from __future__ import annotations

import asyncio
import logging

from yaml import YAMLError

from consts import DEBUG_MODE
from errors import ConfigError
from logsupport import add_stream_handler
from onadaily import Onadaily

if __name__ == "__main__":
    entertoquit = True
    try:
        logger = logging.getLogger("onadaily")
        logger.setLevel(logging.DEBUG)

        if DEBUG_MODE:
            add_stream_handler(logger, True)

        main = Onadaily()
        entertoquit = main.options.common.entertoquit
        asyncio.run(main.run())
    except ConfigError as e:
        logger.exception(f"설정 파일 오류 : {e}\n")
    except YAMLError as e:
        logger.exception(f"설정 파일 분석 중 오류 발생 : {e}\n")
    except Exception as e:
        logger.exception(f"예상치 못한 오류 발생 : {e}\n")

    finally:
        if entertoquit:
            input("종료하려면 Enter를 누르세요...")
