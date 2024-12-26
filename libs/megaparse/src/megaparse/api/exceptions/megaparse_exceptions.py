from fastapi import HTTPException


class HTTPModelNotSupported(HTTPException):
    def __init__(
        self,
        detail: str = "The requested model is not supported yet.",
        headers: dict | None = None,
    ):
        super().__init__(status_code=501, detail=detail, headers=headers)


class HTTPFileNotFound(HTTPException):
    def __init__(
        self,
        message="The UploadFile.filename does not exist and is needed for this operation",
    ):
        super().__init__(status_code=404, detail=message)


class HTTPDownloadError(HTTPException):
    def __init__(self, file_name, message="Failed to download the file"):
        message = f"{file_name} : {message}"
        super().__init__(status_code=400, detail=message)


class HTTPParsingException(HTTPException):
    def __init__(self, file_name, message="Failed to parse the file"):
        message = f"{file_name} : {message}"
        super().__init__(status_code=500, detail=message)


class ParsingException(Exception):
    """Exception raised for errors in the parsing process."""

    def __init__(self, message="An error occurred during parsing"):
        self.message = message
        super().__init__(self.message)
