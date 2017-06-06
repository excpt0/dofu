class DofuError(Exception):
    pass

class RequestError(DofuError):
    pass

class ResponseError(DofuError):
    pass

class UnknownMethodError(DofuError):
    pass
