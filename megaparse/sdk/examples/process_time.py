import asyncio
import os
import time

import numpy as np

from megaparse.sdk import MegaParseSDK


async def process_file(file_path, api_key):
    try:
        t0 = time.perf_counter()
        megaparse = MegaParseSDK(api_key)
        response = await megaparse.file.upload(
            file_path=file_path,
            method="unstructured",  # type: ignore  # unstructured, llama_parser, megaparse_vision
            strategy="fast",
        )
        await megaparse.close()
        return time.perf_counter() - t0
    except Exception as e:
        return 10000


async def test_process_folder(folder_path, api_key):
    import os

    list_process_time = []
    files = os.listdir(folder_path)
    task = []

    for file in files[:10]:
        task.append(process_file(os.path.join(folder_path, file), api_key))

    list_process_time = await asyncio.gather(*task)

    np_list_process_time = np.array(list_process_time)
    print(f"Average time taken: {np_list_process_time.mean}")
    print(f"Median time taken: {np.median(list_process_time)}")
    print(f"Standard deviation of time taken: {np.std(list_process_time)}")
    print(f"Max time taken: {np.max(list_process_time)}")
    print(f"Min time taken: {np.min(list_process_time)}")


if __name__ == "__main__":
    api_key = os.getenv("MEGAPARSE_API_KEY")
    folder_path = "megaparse/sdk/examples/only_pdfs"
    asyncio.run(test_process_folder(folder_path, api_key))
