from setuptools import setup, find_packages

setup(
    name="megaparse",
    version="0.1.0",
    description="A package for parsing various file formats",
    author="Quivr",
    packages=find_packages(),
    install_requires=[
        "python-docx",
        "mammoth",
        "python-pptx",
        "nest-asyncio",
        "llama-parse",
        "pdf2docx",
    ],
)
