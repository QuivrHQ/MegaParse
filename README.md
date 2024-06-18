# MegaParse - Your Mega Parser for every type of documents

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

1. Add your OpenAI API key to the .env file

2. Install poppler on your computer (images and PDFs)

3. Install tesseract on your computer (images and PDFs)

```python
from megaparse.Converter import MegaParse

megaparse = MegaParse(file_path="./test.pdf")
content = megaparse.convert()
print(content)
megaparse.save_md(content, "./test.md")
```

### (Optional) Use LlamaParse for Improved Results

1. Create an account on [Llama Cloud](https://cloud.llamaindex.ai/) and get your API key.

2. Call Megaparse with the `llama_parse_api_key` parameter

```python
from megaparse.Converter import MegaParse

megaparse = MegaParse(file_path="./test.pdf", llama_parse_api_key="llx-your_api_key")
content = megaparse.convert()
print(content)
```

## BenchMark

<!---BENCHMARK-->
| Parser | Diff |
|---|---|
| Megaparse with LLamaParse and GPTCleaner | 84 |
| **Megaparse** | 100 |
| Megaparse with LLamaParse | 104 |
| LLama Parse | 108 |
<!---END_BENCHMARK-->

*Lower is better*

## Next Steps

- [ ] Improve Table Parsing
- [ ] Improve Image Parsing and description
- [ ] Add TOC for Docx
- [ ] Add Hyperlinks for Docx
- [ ] Order Headers for Docx to Markdown


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=QuivrHQ/MegaParse&type=Date)](https://star-history.com/#QuivrHQ/MegaParse&Date)
