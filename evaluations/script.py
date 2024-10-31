from langchain_openai import ChatOpenAI
from megaparse.core.parser.llama import LlamaParser
from megaparse.core.parser.type import StrategyEnum
from megaparse.core.parser.unstructured_parser import UnstructuredParser
from megaparse.core.parser.megaparse_vision import MegaParseVision
from megaparse.core.megaparse import MegaParse
import os
import difflib


if __name__ == "__main__":
    print("---Launching evaluations script---")
    model = ChatOpenAI(model="gpt-4o", api_key=str(os.getenv("OPENAI_API_KEY")))  # type: ignore
    parser_dict = {
        "unstructured": UnstructuredParser(strategy=StrategyEnum.AUTO, model=None),
        "unstructured_with_check_table": UnstructuredParser(
            strategy=StrategyEnum.AUTO,
            model=model,
        ),
        "llama_parser": LlamaParser(api_key=str(os.getenv("LLAMA_CLOUD_API_KEY"))),
        "megaparse_vision": MegaParseVision(model=model),
    }

    base_pdf_path = "tests/data/MegaFake_report.pdf"
    base_md_path = "tests/data/grt_example/MegaFake_report.md"
    with open(base_md_path, "r", encoding="utf-8") as f:
        base_md = f.read()

    score_dict = {}

    for method, parser in parser_dict.items():
        print(f"Method: {method}")
        megaparse = MegaParse(parser=parser)
        result = megaparse.load(file_path=base_pdf_path)
        score_dict[method] = difflib.SequenceMatcher(None, base_md, result).ratio()
        print(f"Score for method {method}: {score_dict[method]}")

    # Sort the results
    sorted_score = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)

    # Generate a table with the results
    benchmark_results = "| Parser | similarity_ratio |\n|---|---|\n"
    for parser, score in sorted_score:
        benchmark_results += f"| {parser} | {score:.2f} |\n"

    print(benchmark_results)

    # Update README.md file
    with open("README.md", "r") as readme_file:
        readme_content = readme_file.read()

    start_marker = "<!---BENCHMARK-->"
    end_marker = "<!---END_BENCHMARK-->"
    start_index = readme_content.find(start_marker) + len(start_marker)
    end_index = readme_content.find(end_marker)

    updated_readme_content = (
        readme_content[:start_index]
        + "\n"
        + benchmark_results
        + readme_content[end_index:]
    )

    with open("README.md", "w") as readme_file:
        readme_file.write(updated_readme_content)
