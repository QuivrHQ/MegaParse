import os
from dataclasses import dataclass
from time import perf_counter

from unstructured.partition.auto import partition


@dataclass
class File:
    file_path: str
    file_name: str
    file_extension: str


def list_files_in_directory(directory_path: str) -> dict[str, list[File]]:
    directory_dict = {}
    for root, _, files in os.walk(directory_path):
        folder_name = os.path.basename(root)
        if len(folder_name) > 0:
            file_list = []
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_extension = os.path.splitext(file_name)[1]
                file_list.append(
                    File(
                        file_path=file_path,
                        file_name=file_name,
                        file_extension=file_extension,
                    )
                )
            directory_dict[folder_name] = file_list

    return directory_dict


def main():
    file_path = "/Users/amine/data/quivr/parsing/native/0b0ab5f4-b654-4846-bd9b-18b3c1075c52.pdf"
    folder_path = "/Users/amine/data/quivr/parsing/"

    list_files = list_files_in_directory(folder_path)

    for folder_name, files in list_files.items():
        print(f"folder: {folder_name}")
        for file in files:
            if file.file_extension == ".pdf":
                s = perf_counter()
                elements = partition(
                    filename=file.file_path,
                    strategy="fast",
                )
                if len(elements) == 0:
                    print(f"\t{file.file_name}:  can't parse ")
                    continue

                e = perf_counter()
                print(f"\t {file.file_name} parsing took: {e-s:.2f}s")


if __name__ == "__main__":
    els = main()
