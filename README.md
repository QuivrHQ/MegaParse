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

<div align="center">
    <img src="https://raw.githubusercontent.com/QuivrHQ/MegaParse/main/images/tables.png" alt="Quivr-logo" width="50%"  style="padding-bottom: 20px"/>
</div>

## Installation

```bash
pip install megaparse
```

## Usage

1. Create an account on [Llama Cloud](https://cloud.llamaindex.ai/) and get your API key.

2. Create a new file in the root directory of the project and name it `.env`.

3. Add the following line to the `.env` file and replace `llx-your_api_key` with your actual API key.

```bash
LLAMA_CLOUD_API_KEY=llx-your_api_key
```

4. Now you can use the following code to convert a PDF to Markdown and save it to a file.

```python
from megaparse import MegaParse

megaparse = MegaParse(file_path="./test.pdf")
content = megaparse.convert()
print(content)
megaparse.save_md(content, "./test.md")
```

## Next Steps

- [ ] Add Unstructured Parser Support
- [ ] Improve Table Parsing
- [ ] Improve Image Parsing and description
- [ ] Add TOC for Docx
- [ ] Add Hyperlinks for Docx
- [ ] Order Headers for Docx to Markdown