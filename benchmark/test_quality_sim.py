import os
import difflib
from pathlib import Path

auto_dir = Path("benchmark/auto")
hi_res_dir = Path("benchmark/hi_res")


def jaccard_similarity(str1, str2):
    if len(str1) == 0 and len(str2) == 0:
        return 1
    # Tokenize the strings into sets of words
    words1 = set(str1.split())
    words2 = set(str2.split())

    # Find intersection and union of the word sets
    intersection = words1.intersection(words2)
    union = words1.union(words2)

    # Compute Jaccard similarity
    return len(intersection) / len(union) if len(union) != 0 else 0


def compare_files(file_name):
    file_path_auto = auto_dir / f"{file_name}.md"
    file_path_hi_res = hi_res_dir / f"{file_name}.md"

    with open(file_path_auto, "r") as f:
        auto_content = f.read()

    with open(file_path_hi_res, "r") as f:
        hi_res_content = f.read()

    if len(auto_content) == 0 and len(hi_res_content) == 0:
        return 1

    similarity = difflib.SequenceMatcher(None, auto_content, hi_res_content).ratio()
    # similarity = jaccard_similarity(auto_content, hi_res_content)

    return similarity


def main():
    files = os.listdir(hi_res_dir)
    print(f"Comparing {len(files)} files...")
    similarity_dict = {}
    for file in files:
        file_name = Path(file).stem
        similarity = compare_files(file_name)
        similarity_dict[file_name] = similarity

    avg_similarity = sum(similarity_dict.values()) / len(similarity_dict)
    print(f"\nAverage similarity: {avg_similarity}\n")

    pass_rate = sum(
        [similarity > 0.9 for similarity in similarity_dict.values()]
    ) / len(similarity_dict)

    print(f"Pass rate: {pass_rate}\n")

    print("Under 0.9 similarity documents:")
    print("-------------------------------")
    for file_name, similarity in similarity_dict.items():
        if similarity < 0.9:
            print(f"{file_name}: {similarity}")


if __name__ == "__main__":
    main()
