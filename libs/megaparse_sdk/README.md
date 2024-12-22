# MegaParse SDK

Welcome to the MegaParse SDK! This SDK provides a convenient interface to interact with the MegaParse API for document processing and URL content extraction.

## Installation

```sh
pip install megaparse-sdk
```

## Prerequisites

1. **API Key**: Obtain your MegaParse API key
2. **Python Version**: Python 3.11 or higher
3. **Environment Variables**:
   ```bash
   MEGAPARSE_API_KEY=your_api_key
   ```

### Usage

Here is an example of how to use the MegaParse SDK:

#### Uploading URLs

```python
import asyncio
import os

from megaparse.sdk import MegaParseSDK

async def upload_url():
    api_key = str(os.getenv("MEGAPARSE_API_KEY"))
    megaparse = MegaParseSDK(api_key)

    url = "https://www.quivr.com"

    # Upload a URL
    url_response = await megaparse.url.upload(url)
    print(f"\n----- URL Response : {url} -----\n")
    print(url_response)

    await megaparse.close()

if __name__ == "__main__":
    asyncio.run(upload_url())
```

#### Uploading Files

```python
import asyncio
import os

from megaparse.sdk import MegaParseSDK

async def upload_file():
    api_key = str(os.getenv("MEGAPARSE_API_KEY"))
    megaparse = MegaParseSDK(api_key)

    file_path = "your/file/path.pdf"
    # Upload a file
    response = await megaparse.file.upload(
        file_path=file_path,
        method="unstructured",  # unstructured, llama_parser, megaparse_vision
        strategy="auto",
    )
    print(f"\n----- File Response : {file_path} -----\n")
    print(response)

    await megaparse.close()

if __name__ == "__main__":
    asyncio.run(upload_file())
```

## Features

- **URL Processing**: Extract and parse content from web pages
- **File Processing**: Parse documents with configurable strategies
- **Async Support**: All operations support async/await
- **Multiple Parser Options**: Choose from various parsing strategies
- **Configurable Behavior**: Fine-tune parsing parameters

## Advanced Usage

### Configuring Parser Strategy

```python
import asyncio
from megaparse_sdk import MegaParseSDK
from megaparse_sdk.schema.parser_config import ParserType, StrategyEnum

async def process_with_strategy():
    sdk = MegaParseSDK(api_key="your_api_key")
    
    # Use high-resolution parsing for complex documents
    response = await sdk.file.upload(
        file_path="complex.pdf",
        method=ParserType.MEGAPARSE_VISION,
        strategy=StrategyEnum.HI_RES
    )
    
    await sdk.close()
```

### Batch Processing

```python
async def batch_process():
    sdk = MegaParseSDK(api_key="your_api_key")
    
    # Process multiple files concurrently
    files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    tasks = [
        sdk.file.upload(file_path=f) 
        for f in files
    ]
    
    results = await asyncio.gather(*tasks)
    await sdk.close()
```

## Troubleshooting

Common issues and solutions:

1. **Connection Errors**
   - Verify `MEGAPARSE_API_KEY` is set correctly
   - Check network connectivity
   - Ensure firewall allows outbound connections

2. **File Processing Errors**
   - Verify file exists and is readable
   - Check file format is supported
   - Ensure file size is within limits

3. **Rate Limiting**
   - Implement exponential backoff
   - Use batch processing wisely
   - Monitor API usage

## Support

Need help? Check out:
- [Main Documentation](../../../README.md)
- [API Documentation](http://localhost:8000/docs)
- [GitHub Issues](https://github.com/QuivrHQ/MegaParse/issues)

We hope you find the MegaParse SDK useful for your projects!

_Quivr Team_
