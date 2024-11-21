class ModelNotSupported(Exception):
    def __init__(
        self,
        message: str = "The requested model is not supported yet.",
    ):
        super().__init__(message)


class MemoryLimitExceeded(Exception):
    def __init__(self, message="The service is under high memory pressure"):
        super().__init__(message)


class InternalServiceError(Exception):
    def __init__(self, message="Internal service error occured"):
        super().__init__(message)


class DownloadError(Exception):
    def __init__(self, message="Failed to download the file"):
        super().__init__(message)


class ParsingException(Exception):
    def __init__(self, message="An error occurred during parsing"):
        super().__init__(message)
