class ConfigError(Exception):
    pass


class ParseError(Exception):
    pass


class LoginFailedError(Exception):
    def __init__(self, message) -> None:
        message = f"❌ 로그인 중 실패\n\t-{message}"
        super().__init__(message)


class StampFailedError(Exception):
    def __init__(self, message) -> None:
        message = f"❌ 출석체크 중 실패\n\t-{message}"
        super().__init__(message)


class AlreadyStamped(Exception):
    pass


class HotDealDataNotFoundError(Exception):
    pass


class HotDealTableParseError(Exception):
    pass
