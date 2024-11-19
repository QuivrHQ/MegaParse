class ModelNotSupported(Exception):
    def __init__(
        self,
        message: str = "The requested model is not supported yet.",
    ):
        super().__init__(message)


class DownloadError(Exception):
    def __init__(self, message="Failed to download the file"):
        super().__init__(message)


class ParsingException(Exception):
    """Exception raised for errors in the parsing process."""

    def __init__(self, message="An error occurred during parsing"):
        super().__init__(message)
