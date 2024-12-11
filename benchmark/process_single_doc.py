import asyncio
import time
from pathlib import Path

import numpy as np
from megaparse import MegaParse
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse_sdk.schema.parser_config import StrategyEnum

N_TRY = 1


async def process_file(megaparse: MegaParse, file_path: str | Path):
    try:
        t0 = time.perf_counter()
        _ = await megaparse.aload(
            file_path=file_path,
        )
        total = time.perf_counter() - t0
        return total
    except Exception as e:
        print(f"Exception occured: {e}")
        return None


async def test_process_file(file: str | Path):
    parser = UnstructuredParser(strategy=StrategyEnum.HI_RES)
    megaparse = MegaParse(parser=parser)
    task = []
    for _ in range(N_TRY):
        task.append(process_file(megaparse, file))
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
    folder_path = "/Users/amine/data/quivr/parsing/scanned/machine.pdf"
    asyncio.run(test_process_file(folder_path))
