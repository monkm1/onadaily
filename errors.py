class ConfigError(Exception):
    pass


class ParseError(Exception):
    pass


class LoginFailedError(Exception):
    pass


class StampFailedError(Exception):
    pass


class AlreadyStamped(Exception):
    pass


class HotDealDataNotFoundError(Exception):
    pass


class HotDealTableParseError(Exception):
    pass
