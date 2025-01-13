import os

import pytest
from megaparse.parser.doctr_parser import DoctrParser
from megaparse.parser.llama import LlamaParser
from megaparse.parser.megaparse_vision import MegaParseVision
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse_sdk.schema.extensions import FileExtension

PARSER_LIST = [
    UnstructuredParser,
    # DoctrParser,
]


@pytest.mark.parametrize("parser", PARSER_LIST)
@pytest.mark.parametrize("extension", list(FileExtension))
def test_sync_parser(parser, extension):
    directory = "./tests/supported_docs"
    file_path = next(
        (
            os.path.join(root, file)
            for root, _, files in os.walk(directory)
            for file in files
            if file.endswith(extension.value)
        ),
        None,
    )
    if file_path is None:
        pytest.fail(f"No file with extension {extension.value} found in {directory}")

    myparser = parser()
    if extension in myparser.supported_extensions:
        response = myparser.convert(file_path)

        assert response
        assert len(str(response)) > 0
    else:
        with pytest.raises(ValueError):
            myparser.convert(file_path)
