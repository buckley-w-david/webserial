class WebserialError(Exception):
    pass


class EqualChapterError(WebserialError):
    pass


class NoChaptersFoundError(WebserialError):
    pass


class LocalAheadOfRemoteError(WebserialError):
    pass
