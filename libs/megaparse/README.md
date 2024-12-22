# MegaParse Core Library

The core package of MegaParse provides the fundamental parsing capabilities and orchestration for document processing.

## Overview

The MegaParse core library implements:
- Document parsing strategies
- Parser selection and configuration
- Format checking and validation
- Markdown processing and cleanup

## Key Components

### MegaParse Class
The main orchestrator that handles:
- File loading and validation
- Parser selection and initialization
- Document processing workflow
- Output formatting and saving

### Parsers
Available parsing implementations:
- `UnstructuredParser`: Basic document parsing
- `MegaParseVision`: AI-powered parsing with GPT-4V
- `LlamaParser`: Enhanced PDF parsing
- `DoctrParser`: OCR-based parsing

### Usage

```python
from megaparse import MegaParse
from megaparse.parser.base import BaseParser
from megaparse.parser.strategy import StrategyEnum

# Choose a parsing strategy
strategy = StrategyEnum.AUTO  # or FAST, HI_RES

# Initialize with your preferred parser
parser = YourChosenParser()  # implements BaseParser
megaparse = MegaParse(parser)

# Parse a document
result = megaparse.load("./document.pdf", strategy=strategy)
```

### Creating Custom Parsers

Implement the `BaseParser` class to create your own parser:

```python
from megaparse.parser.base import BaseParser
from megaparse.parser.strategy import StrategyEnum

class CustomParser(BaseParser):
    def convert(self, file_path: str, strategy: StrategyEnum = StrategyEnum.AUTO) -> str:
        # Implement your parsing logic here
        pass

    async def aconvert(self, file_path: str, strategy: StrategyEnum = StrategyEnum.AUTO) -> str:
        # Implement async parsing logic here
        pass
```

For environment setup and installation instructions, see the [main project README](../../../README.md).
