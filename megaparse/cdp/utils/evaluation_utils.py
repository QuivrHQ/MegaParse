from enum import Enum
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel
import difflib

class MappingType(BaseModel):
    "Mapping dict from source to target name"
    matches: dict[str, str]

class MethodEnum(str, Enum):
    llm = "llm"
    fuzzy = "fuzzy"

def fuzzy_match(name, choices, threshold=0.8):
            matches = [g_name for g_name in choices if name in g_name]
            if matches:
                return matches
            
            matches = difflib.get_close_matches(name, choices, n=1, cutoff=threshold)
            if matches:
                return matches
            else:
                return None
            
def map_keys(source_keys: list[str], target_keys: list[str], method: MethodEnum = MethodEnum.llm):
    if method == MethodEnum.llm:
        model = ChatOpenAI(model="gpt-4o", temperature=0.0)

        # Set up a parser + inject instructions into the prompt template.
        parser = PydanticOutputParser(pydantic_object=MappingType)

        prompt = PromptTemplate(
            template="Translate the following mapping from target to source keys (if there are no equivalent set the value to 'no_match'). Map as much as possible if they could be the same.:\n\n{format_instructions}\n\nTarget keys: {target_keys}\nSource keys: {source_keys}\n\nTranslated mapping:",
            input_variables=["source_keys", "target_keys"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # And a query intended to prompt a language model to populate the data structure.
        prompt_and_model = prompt | model
        mapping = prompt_and_model.invoke({"source_keys": ",\n".join(source_keys), "target_keys": ",\n".join(target_keys)})
        structured_mapping: MappingType = parser.invoke(mapping)
        structured_mapping_copy = structured_mapping.matches

        for key in target_keys:
            if key not in structured_mapping.matches or structured_mapping.matches[key] == "no_match":
                print(f"{key} -> no_match")
                structured_mapping_copy[key] = "no_match"
                continue
            assert structured_mapping.matches[key] in source_keys or structured_mapping.matches[key] == "no_match", f"Key {key} not found in target keys"
            structured_mapping_copy[key] = structured_mapping.matches[key]

    else: 
        structured_mapping_copy = {}
        for target_name in target_keys:
            matched_name = fuzzy_match(target_name, source_keys)
            if matched_name:
                structured_mapping_copy[target_name] = matched_name
            else:
                structured_mapping_copy[target_name] = "no_match"

    return structured_mapping_copy

    