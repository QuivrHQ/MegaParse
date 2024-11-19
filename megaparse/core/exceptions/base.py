class ParsingException(Exception):
    """Exception raised for errors in the parsing process."""

    def __init__(self, message="An error occurred during parsing"):
        self.message = message
        super().__init__(self.message)
