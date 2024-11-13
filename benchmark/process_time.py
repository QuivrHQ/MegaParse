import asyncio
import os
import time

import numpy as np

from megaparse.sdk import MegaParseSDK


async def process_file(megaparse: MegaParseSDK, file_path):
    try:
        t0 = time.perf_counter()
        response = await megaparse.file.upload(
            file_path=file_path,
            method="unstructured",  # type: ignore  # unstructured, llama_parser, megaparse_vision
            strategy="auto",
        )
        total = time.perf_counter() - t0
        return total
    except Exception as e:
        print(f"Exception occured: {e}")
        return None


async def test_process_folder(folder_path, api_key):
    import os

    list_process_time = []
    files = os.listdir(folder_path)
    task = []

    megaparse = MegaParseSDK(api_key)
    for file in files:
        task.append(process_file(megaparse, os.path.join(folder_path, file)))
    list_process_time = await asyncio.gather(*task)

    n_errors = sum([t is None for t in list_process_time])
    list_process_time = [t for t in list_process_time if t is not None]

    np_list_process_time = np.array(list_process_time)
    print(f"All errors : {n_errors}")
    print(f"Average time taken: {np_list_process_time.mean()}")
    print(f"Median time taken: {np.median(list_process_time)}")
    print(f"Standard deviation of time taken: {np.std(list_process_time)}")
    print(f"Max time taken: {np.max(list_process_time)}")
    print(f"Min time taken: {np.min(list_process_time)}")


if __name__ == "__main__":
    api_key = os.getenv("MEGAPARSE_API_KEY")
    # folder_path = "megaparse/sdk/examples/only_pdfs"
    folder_path = "/Users/amine/data/quivr/only_pdfs/"
    asyncio.run(test_process_folder(folder_path, api_key))
