import traceback

from yaml import YAMLError

from classes import ConfigError
from config import options
from onadaily import Onadaily

if __name__ == "__main__":
    try:
        main = Onadaily()
        main.run()
    except ConfigError as ex:
        print("설정 파일 오류 :\n", ex)
    except YAMLError:
        print("설정 파일 분석 중 오류 발생 :")
        print(traceback.format_exc())

    if options.common.entertoquit:
        input("종료하려면 Enter를 누르세요...")
