from fastapi import HTTPException


class HTTPFileNotFound(HTTPException):
    def __init__(self, message="File name not found"):
        super().__init__(status_code=404, detail=message)


class HTTPDownloadError(HTTPException):
    def __init__(self, file_name, message="Failed to download the file"):
        message = f"{file_name} : {message}"
        super().__init__(status_code=400, detail=message)


class HTTPParsingException(HTTPException):
    def __init__(self, file_name, message="Failed to parse the file"):
        message = f"{file_name} : {message}"
        super().__init__(status_code=500, detail=message)
