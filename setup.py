from setuptools import setup, find_packages

setup(
    name="megaparse",
    version="0.0.1",
    description="A package for parsing various file formats",
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
    ],
)
