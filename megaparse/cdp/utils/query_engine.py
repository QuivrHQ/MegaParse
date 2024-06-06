from enum import Enum
from pathlib import Path
from llama_index.readers.file import MarkdownReader
from llama_index.core.node_parser import MarkdownNodeParser
import asyncio
import nest_asyncio
import uvloop
import os
import pickle
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import BaseNode, IndexNode, TextNode, MetadataMode
from llama_index.core.query_engine import RetrieverQueryEngine
from langchain_core.pydantic_v1 import BaseModel, Field
from llama_index.llms.openai import OpenAI


# class Ingredient(BaseModel):
#     detailed_answer: str = Field(description="Detailed answer with explanations")
#     decision: str = Field(description="Decision made : authorized / To avoid/ Forbidden'")

class DecisionEnum(str, Enum):
    authorized = 'Authorized'
    to_avoid = 'To Avoid'
    forbidden = 'Forbidden'

class Ingredient(BaseModel):
    """Represents an ingredient and its associated decision."""
    name: str = Field(description="Name of the ingredient")
    detailed_answer: str = Field(description="Detailed answer with explanations")
    decision: DecisionEnum = Field(description="Decision made: authorized / to avoid / forbidden")


def get_query_engine(source_path: Path, top_k: int = 5):
    """Get a query engine for markdown files."""
    if not isinstance(asyncio.get_event_loop(), uvloop.Loop):
        nest_asyncio.apply()

    reader = MarkdownReader()
    md_doc = reader.load_data(source_path)

    node_parser = MarkdownNodeParser()

    if not os.path.exists("./charte.pkl"):
        raw_nodes_charte = node_parser.get_nodes_from_documents(md_doc, show_progress= False)
        cleaned_nodes_charte: list[BaseNode] = [node for node in raw_nodes_charte if node.get_content(metadata_mode=MetadataMode.EMBED) != "" ]
        pickle.dump(cleaned_nodes_charte, open("./charte.pkl", "wb"))
    else:
        cleaned_nodes_charte = pickle.load(open("./charte.pkl", "rb"))

    llm = OpenAI(model="gpt-4o", temperature=0.0) #0.1

    vector_index = VectorStoreIndex(cleaned_nodes_charte)
    #vector_retriever = vector_index.as_retriever(similarity_top_k=top_k, outpuy_cls = Ingredient)

    #query_engine = RetrieverQueryEngine.from_args(vector_retriever)
    query_engine = vector_index.as_query_engine(output_cls = Ingredient, similarity_top_k=top_k, llm=llm, response_mode = "tree_summarize")

    return query_engine



    
