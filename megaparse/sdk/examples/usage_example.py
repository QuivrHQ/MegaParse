from sdk import MegaParseSDK

if __name__ == "__main__":
    api_key = "your_api_key_here"  # Replace with actual API key
    megaparse = MegaParseSDK(api_key)

    # Upload a file
    response = megaparse.file.upload(
        file_path="sample.pdf",
        method="unstructured",
        strategy="auto",
        language="english",
        model_name="gpt-4o",
    )
    print(response)

    # Upload a URL
    url_response = megaparse.url.upload("https://example.com")
    print(url_response)

    # Close the client session when done
    megaparse.close()
