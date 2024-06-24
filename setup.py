from setuptools import setup, find_packages

setup(
    name="megaparse",
    version="0.0.13",
    description="Parse complex files (PDF,Docx,PPTX) for LLM consumption",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Quivr",
    packages=find_packages(),
    install_requires=[
        "python-docx",
        "mammoth",
        "python-pptx",
        "nest-asyncio",
        "llama-parse",
        "pdf2docx",
        "unstructured",
        "markdownify"
    ],
)
