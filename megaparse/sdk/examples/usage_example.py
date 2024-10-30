from megaparse.sdk import MegaParseSDK
import asyncio


async def main():
    api_key = "your_api_key_here"  # Replace with actual API key
    megaparse = MegaParseSDK(api_key)

    # # Upload a URL
    # url_response = megaparse.url.upload("https://www.quivr.com")
    # print(url_response)

    # Upload a file
    response = await megaparse.file.upload(
        file_path="megaparse/sdk/pdf/MegaFake_report.pdf",
        method="unstructured",  # type: ignore  # unstructured, llama_parser, megaparse_vision
        strategy="auto",
    )

    print(response)
    await megaparse.close()


if __name__ == "__main__":
    asyncio.run(main())
