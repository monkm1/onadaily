from __future__ import annotations

import asyncio
import logging

from yaml import YAMLError

from config import Options
from consts import DEBUG_MODE
from errors import ConfigError
from logsupport import LogCaptureContext, LoggingInfo, add_stream_handler, save_log
from onadaily import Onadaily

if __name__ == "__main__":
    entertoquit = True
    log_capture = None
    try:
        logger = logging.getLogger("onadaily")
        logger.setLevel(logging.DEBUG)
        log_capture = LogCaptureContext(logger, "main")

        if DEBUG_MODE:
            add_stream_handler(logger, True)

        with log_capture:
            options = Options()
            entertoquit = options.common.entertoquit
            main = Onadaily()
        asyncio.run(main.run())
    except ConfigError as e:
        logger.exception(f"설정 파일 오류 : {e}\n")
    except YAMLError as e:
        logger.exception(f"설정 파일 분석 중 오류 발생 : {e}\n")
    except Exception as e:
        logger.exception(f"예상치 못한 오류 발생 : {e}\n")

    finally:
        if log_capture is not None and log_capture.exc_type is not None:
            save_log(LoggingInfo(logcontext=log_capture))
        elif entertoquit:
            input("종료하려면 Enter를 누르세요...")
