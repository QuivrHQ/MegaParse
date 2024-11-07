## MegaParse SDK

Welcome to the MegaParse SDK! This SDK allows you to easily interact with the MegaParse API to upload URLs and files for processing.

### Installation

To install the MegaParse SDK, use pip:

```sh
pip install megaparse-sdk
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

### Features

- **Upload URLs**: Easily upload URLs for processing.
- **Upload Files**: Upload files with different processing methods and strategies.

### Getting Started

1. **Set up your API key**: Make sure to set the `MEGAPARSE_API_KEY` environment variable with your MegaParse API key.
2. **Run the example**: Use the provided example to see how to upload URLs and files.

For more details, refer to the [usage example](#file:usage_example.py-context).

We hope you find the MegaParse SDK useful for your projects!

Enjoy, *Quivr Team* ! 