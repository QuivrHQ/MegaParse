# MegaParse - Your Parser for every type of documents

<div align="center">
    <img src="https://raw.githubusercontent.com/QuivrHQ/MegaParse/main/logo.png" alt="Quivr-logo" width="30%"  style="border-radius: 50%; padding-bottom: 20px"/>
</div>

MegaParse is a powerful and versatile parser that can handle various types of documents with ease. Whether you're dealing with text, PDFs, Powerpoint presentations, Word documents MegaParse has got you covered. Focus on having no information loss during parsing.

## Key Features 🎯

- **Versatile Parser**: MegaParse is a powerful and versatile parser that can handle various types of documents with ease.
- **No Information Loss**: Focus on having no information loss during parsing.
- **Fast and Efficient**: Designed with speed and efficiency at its core.
- **Wide File Compatibility**: Supports Text, PDF, Powerpoint presentations, Excel, CSV, Word documents.
- **Open Source**: Freedom is beautiful, and so is MegaParse. Open source and free to use.

## Support

- Files: ✅ PDF ✅ Powerpoint ✅ Word
- Content: ✅ Tables ✅ TOC ✅ Headers ✅ Footers ✅ Images

### Example

https://github.com/QuivrHQ/MegaParse/assets/19614572/1b4cdb73-8dc2-44ef-b8b4-a7509bc8d4f3

## Installation

```bash
pip install megaparse 
```

## Usage

1. Add your OpenAI or Anthropic API key to the .env file

2. Install poppler on your computer (images and PDFs)

3. Install tesseract on your computer (images and PDFs)

4. If you have a mac, you also need to install libmagic ```brew install libmagic```


```python
from megaparse.core.megaparse import MegaParse
from langchain_openai import ChatOpenAI
from megaparse.core.parser.unstructured_parser import UnstructuredParser

model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))  # or any langchain compatible Chat Models
parser = UnstructuredParser(model=model)
megaparse = MegaParse(parser)
response = megaparse.load("./test.pdf")
print(response)
megaparse.save("./test.md") #saves the last processed doc in md format
```

### Use MegaParse Vision

* Change the parser to MegaParseVision

```python
from megaparse.core.megaparse import MegaParse
from langchain_openai import ChatOpenAI
from megaparse.core.parser.megaparse_vision import MegaParseVision

model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
parser = MegaParseVision(model=model)
megaparse = MegaParse(parser)
response = megaparse.load("./test.pdf")
print(response)
megaparse.save("./test.md")

```
**Note**: The model supported by MegaParse Vision are the multimodal ones such as claude 3.5, claude 4, gpt-4o and gpt-4.

### (Optional) Use LlamaParse for Improved Results

1. Create an account on [Llama Cloud](https://cloud.llamaindex.ai/) and get your API key.

2. Change the parser to LlamaParser

```python
from megaparse.core.megaparse import MegaParse
from langchain_openai import ChatOpenAI
from megaparse.core.parser.llama import LlamaParser

parser = LlamaParser(api_key = os.getenv("LLAMA_CLOUD_API_KEY"))
megaparse = MegaParse(parser)
response = megaparse.load("./test.pdf")
print(response)
megaparse.save("./test.md") #saves the last processed doc in md format
```

## Use as an API
There is a MakeFile for you, simply use :
```make dev```
at the root of the project and you are good to go.

See localhost:8000/docs for more info on the different endpoints !

## BenchMark

<!---BENCHMARK-->
| Parser | similarity_ratio |
|---|---|
| megaparse_vision | 0.87 |
| unstructured_with_check_table | 0.77 |
| unstructured | 0.59 |
| llama_parser | 0.33 |
<!---END_BENCHMARK-->

_Higher the better_

Note: Want to evaluate and compare your Megaparse module with ours ? Please add your config in ```evaluations/script.py``` and then run ```python evaluations/script.py```. If it is better, do a PR, I mean, let's go higher together 🚀.

## In Construction 🚧
- Improve table checker
- Create Checkers to add **modular postprocessing** ⚙️
- Add Structured output, **let's get computer talking** 🤖



## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=QuivrHQ/MegaParse&type=Date)](https://star-history.com/#QuivrHQ/MegaParse&Date)
