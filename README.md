# MegaParse - Your Parser for every type of documents

<div align="center">
    <img src="https://raw.githubusercontent.com/QuivrHQ/MegaParse/main/logo.png" alt="Quivr-logo" width="30%"  style="border-radius: 50%; padding-bottom: 20px"/>
</div>

MegaParse is a powerful and versatile parser that can handle various types of documents with ease. Whether you're dealing with text, PDFs, Powerpoint presentations, Word documents MegaParse has got you covered. Focus on having no information loss during parsing.

## Quick Start Guide 🚀

1. **Prerequisites**
   - Python >= 3.11
   - Poppler (for PDF support)
   - Tesseract (for OCR support)
   - libmagic (for file type detection)

2. **Installation**
   ```bash
   # Install system dependencies (Ubuntu/Debian)
   sudo apt-get update
   sudo apt-get install -y poppler-utils tesseract-ocr libmagic1

   # Install system dependencies (macOS)
   brew install poppler tesseract libmagic

   # Install MegaParse
   pip install megaparse
   ```

3. **Environment Setup**
   ```bash
   # Create a .env file with your API keys
   OPENAI_API_KEY=your_openai_key  # Required for MegaParseVision
   LLAMA_CLOUD_API_KEY=your_llama_key  # Optional, for LlamaParser
   ```

## Project Architecture 🏗️

MegaParse is organized into two main components:

- **megaparse**: Core parsing library with multiple parsing strategies
  - UnstructuredParser: Basic document parsing
  - MegaParseVision: Advanced parsing with GPT-4V
  - LlamaParser: Enhanced PDF parsing using LlamaIndex
  - DoctrParser: OCR-based parsing

- **megaparse_sdk**: Client SDK for interacting with the MegaParse API

## Key Features 🎯

- **Versatile Parser**: MegaParse is a powerful and versatile parser that can handle various types of documents with ease.
- **No Information Loss**: Focus on having no information loss during parsing.
- **Fast and Efficient**: Designed with speed and efficiency at its core.
- **Wide File Compatibility**: Supports Text, PDF, Powerpoint presentations, Excel, CSV, Word documents.
- **Open Source**: Freedom is beautiful, and so is MegaParse. Open source and free to use.

## Support

- Files: ✅ PDF ✅ Powerpoint ✅ Word
- Content: ✅ Tables ✅ TOC ✅ Headers ✅ Footers ✅ Images

### Example

https://github.com/QuivrHQ/MegaParse/assets/19614572/1b4cdb73-8dc2-44ef-b8b4-a7509bc8d4f3

## Usage Examples 💡

### Basic Usage with UnstructuredParser
The UnstructuredParser is the default parser that works with most document types without requiring additional API keys:

```python
from megaparse import MegaParse
from megaparse.parser.unstructured_parser import UnstructuredParser

# Initialize the parser
parser = UnstructuredParser()
megaparse = MegaParse(parser)

# Parse a document
response = megaparse.load("./document.pdf")
print(response)

# Save the parsed content as markdown
megaparse.save("./output.md")
```

### Advanced Usage with MegaParseVision
MegaParseVision uses advanced AI models for improved parsing accuracy:

```python
from megaparse import MegaParse
from langchain_openai import ChatOpenAI
from megaparse.parser.megaparse_vision import MegaParseVision

# Initialize with GPT-4V
model = ChatOpenAI(model="gpt-4v", api_key=os.getenv("OPENAI_API_KEY"))
parser = MegaParseVision(model=model)
megaparse = MegaParse(parser)

# Parse with advanced features
response = megaparse.load("./complex_document.pdf")
print(response)
megaparse.save("./output.md")
```

**Supported Models**: MegaParseVision works with multimodal models:
- OpenAI: GPT-4V
- Anthropic: Claude 3 Opus, Claude 3 Sonnet
- Custom models (implement the BaseModel interface)

### Parsing Strategies
MegaParse supports different parsing strategies to balance speed and accuracy:

- **AUTO**: Automatically selects the best strategy based on document type
- **FAST**: Optimized for speed, best for simple documents
- **HI_RES**: Maximum accuracy, recommended for complex documents

```python
from megaparse.parser.strategy import StrategyEnum

# Use high-resolution parsing
response = megaparse.load("./complex_document.pdf", strategy=StrategyEnum.HI_RES)
```

## Running the API Server 🌐

### Using Docker (Recommended)
```bash
# Build and start the API server
docker compose build
docker compose up

# For GPU support
docker compose -f docker-compose.gpu.yml up
```

### Manual Setup
```bash
# Install dependencies using UV (recommended)
UV_INDEX_STRATEGY=unsafe-first-match uv pip sync

# Start the API server
uv pip run uvicorn megaparse.api.app:app
```

The API will be available at http://localhost:8000 with interactive documentation at http://localhost:8000/docs

## BenchMark

<!---BENCHMARK-->
| Parser                        | similarity_ratio |
| ----------------------------- | ---------------- |
| megaparse_vision              | 0.87             |
| unstructured_with_check_table | 0.77             |
| unstructured                  | 0.59             |
| llama_parser                  | 0.33             |
<!---END_BENCHMARK-->

_Higher the better_

Note: Want to evaluate and compare your Megaparse module with ours ? Please add your config in ```evaluations/script.py``` and then run ```python evaluations/script.py```. If it is better, do a PR, I mean, let's go higher together .

## In Construction 🚧
- Improve table checker
- Create Checkers to add **modular postprocessing** ⚙️
- Add Structured output, **let's get computer talking** 🤖



## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=QuivrHQ/MegaParse&type=Date)](https://star-history.com/#QuivrHQ/MegaParse&Date)
