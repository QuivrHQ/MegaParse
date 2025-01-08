from pathlib import Path
from megaparse.formatter.structured_formatter import StructuredFormatter
from megaparse.models.document import Document
from pydantic import BaseModel


class CustomStructuredFormatter(StructuredFormatter):
    def format(
        self,
        document: Document,
        file_path: Path | str | None = None,
    ) -> str:
        """
        Structure the file using an AI language model.
        Args:
            text: The text to format.
            file_path: The file path of the text.
            model: The AI language model to use for formatting.
        Returns:
            The structured text.
        """
        if not self.model:
            raise ValueError("A Model is needed to use the CustomStructuredFormatter.")
        print("Formatting text using CustomStructuredFormatter...")
        text = str(document)
        if len(text) < 0:
            raise ValueError(
                "A non empty text is needed to format text using CustomStructuredFormatter."
            )
        if not self.output_model:
            raise ValueError(
                "An output model is needed to structure text using CustomStructuredFormatter."
            )

        structured_model = self.model.with_structured_output(self.output_model)  # type: ignore

        formatted_text = structured_model.invoke(
            f"Parse the text in a structured format: {text}"
        )
        assert isinstance(formatted_text, BaseModel), "Model output is not a BaseModel."

        return formatted_text.model_dump_json()

    async def aformat(
        self,
        document: Document,
        file_path: Path | str | None = None,
    ) -> str:
        """
        Asynchronously structure the file using an AI language model.
        Args:
            text: The text to format.
            file_path: The file path of the text.
            model: The AI language model to use for formatting.
        Returns:
            The structured text.
        """
        if not self.model:
            raise ValueError("A Model is needed to use the CustomStructuredFormatter.")
        print("Formatting text using CustomStructuredFormatter...")
        text = str(document)

        if len(text) < 0:
            raise ValueError(
                "A non empty text is needed to format text using CustomStructuredFormatter."
            )
        if not self.output_model:
            raise ValueError(
                "An output model is needed to structure text using CustomStructuredFormatter."
            )

        structured_model = self.model.with_structured_output(self.output_model)  # type: ignore

        formatted_text = await structured_model.ainvoke(
            f"Parse the text in a structured format: {text}"
        )
        assert isinstance(formatted_text, BaseModel), "Model output is not a BaseModel."

        return formatted_text.model_dump_json()
