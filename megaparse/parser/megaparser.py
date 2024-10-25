from pathlib import Path


class MegaParser:
    """Mother Class for all the parsers [Unstructured, LlamaParse, MegaParseVision]"""

    async def convert(self, file_path: str | Path, **kwargs) -> str:
        """
        Convert the given file to a specific format.

        Args:
            file_path (str | Path): The path to the file to be converted.
            **kwargs: Additional keyword arguments for the conversion process.

        Returns:
            str: The result of the conversion process.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method")
