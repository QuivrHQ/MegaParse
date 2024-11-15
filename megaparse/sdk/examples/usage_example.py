import asyncio
import os

from megaparse.sdk.megaparse_sdk import MegaParseSDK


async def main():
    api_key = str(os.getenv("MEGAPARSE_API_KEY"))
    megaparse = MegaParseSDK(api_key)

    url = "https://www.quivr.com"

    # Upload a URL
    url_response = await megaparse.url.upload(url)
    print(f"\n----- URL Response : {url} -----\n")
    print(url_response)

    file_path = "megaparse/sdk/pdf/MegaFake_report.pdf"
    # Upload a file
    response = await megaparse.file.upload(
        file_path=file_path,
        method="unstructured",  # type: ignore  # unstructured, llama_parser, megaparse_vision
        strategy="fast",
    )
    print(f"\n----- File Response : {file_path} -----\n")
    print(response)
    await megaparse.close()


if __name__ == "__main__":
    asyncio.run(main())
