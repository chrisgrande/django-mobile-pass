class MobilePassError(Exception):
    pass


class InvalidPass(MobilePassError):
    pass


class InvalidConfig(MobilePassError):
    pass


class ImageNotFound(MobilePassError):
    pass


class InvalidCertificate(MobilePassError):
    pass


class CannotDownload(MobilePassError):
    pass


class GoogleWalletRequestFailed(MobilePassError):
    def __init__(self, message: str, *, status: int | None = None, payload: dict | None = None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


class AppleWalletRequestFailed(MobilePassError):
    def __init__(self, message: str, *, status: int | None = None, payload: dict | None = None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


class PlatformDoesntSupport(MobilePassError):
    pass
