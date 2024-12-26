### (Optional) Use LlamaParse for Improved Results

1. Create an account on [Llama Cloud](https://cloud.llamaindex.ai/) and get your API key.

2. Change the parser to LlamaParser

```python
from megaparse import MegaParse
from langchain_openai import ChatOpenAI
from megaparse.parser.llama_parser import LlamaParser

parser = LlamaParser(api_key = os.getenv("LLAMA_CLOUD_API_KEY"))
megaparse = MegaParse(parser)
response = megaparse.load("./test.pdf")
print(response)
megaparse.save("./test.md") #saves the last processed doc in md format
```