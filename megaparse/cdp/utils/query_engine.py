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

    vector_index = VectorStoreIndex(cleaned_nodes_charte)
    vector_retriever = vector_index.as_retriever(similarity_top_k=top_k)

    query_engine = RetrieverQueryEngine.from_args(vector_retriever)

    return query_engine



    
