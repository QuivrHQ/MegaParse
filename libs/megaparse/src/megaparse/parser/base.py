from abc import ABC, abstractmethod
from pathlib import Path
from typing import IO

from megaparse_sdk.schema.extensions import FileExtension


class BaseParser(ABC):
    """Abstract base class defining the interface for all MegaParse document parsers.
    
    This class serves as the foundation for implementing document parsers in the MegaParse ecosystem.
    Each parser implementation must provide both synchronous and asynchronous conversion methods
    and specify their supported file extensions.

    Attributes:
        supported_extensions (List[FileExtension]): List of file extensions that this parser can handle.
            Must be overridden by subclasses to specify which file types they support.

    Implementation Notes:
        - Subclasses must implement both convert() and aconvert() methods
        - File extension validation is handled automatically by check_supported_extension()
        - Parsers should handle both file paths and file objects for flexibility
        - Error handling should be consistent across all implementations

    Example:
        ```python
        class CustomParser(BaseParser):
            supported_extensions = [FileExtension.PDF, FileExtension.DOCX]
            
            async def aconvert(self, file_path: str, **kwargs) -> str:
                # Implement async parsing logic
                pass
                
            def convert(self, file_path: str, **kwargs) -> str:
                # Implement sync parsing logic
                pass
        ```
    """

    supported_extensions = []

    def check_supported_extension(
        self, file_extension: FileExtension | None, file_path: str | Path | None = None
    ):
        if not file_extension and not file_path:
            raise ValueError(
                "Either file_path or file_extension must be provided for {self.__class__.__name__}"
            )
        if file_path and not file_extension:
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            file_extension = FileExtension(file_path.suffix)
        if file_extension not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file extension {file_extension.value} for {self.__class__.__name__}"
            )

    @abstractmethod
    async def aconvert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extension: FileExtension | None = None,
        **kwargs,
    ) -> str:
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

    @abstractmethod
    def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        file_extension: FileExtension | None = None,
        **kwargs,
    ) -> str:
        """Synchronously convert a document to markdown format.

        This method provides the synchronous interface for document parsing.
        Implementations should handle both file paths and file objects,
        converting the document content to a well-formatted markdown string.

        Args:
            file_path (str | Path | None): Path to the document file
            file (IO[bytes] | None): File object containing document data
            file_extension (FileExtension | None): Explicit file extension
            **kwargs: Implementation-specific arguments like:
                - batch_size: Number of pages to process at once
                - language: Target language for parsing
                - strategy: Parsing strategy selection

        Returns:
            str: Markdown-formatted document content

        Raises:
            NotImplementedError: If not implemented by subclass
            ValueError: If neither file_path nor file is provided
            ValueError: If file extension is not supported
            
        Note:
            - Either file_path or file must be provided
            - File extension validation is automatic
            - Implementations should handle cleanup of temporary files
            - May block for long-running operations
            - Consider using aconvert for better performance
        """
        raise NotImplementedError("Subclasses should implement this method")
