from pathlib import Path
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import pandas as pd
from bs4 import BeautifulSoup

GENERIC_PROMPT = """You will be generating questions to verify the compliance of items based on a provided document. Here is the document:
<document>
{DOCUMENT}
</document>

<document_context>
{DOCUMENT_CONTEXT}
</document_context>

Please follow these steps to generate the questions:

Carefully review the document and items table to understand the context and requirements. Review the input language to know in which language you should generate the questions.
Extract the individual raw items from the items table. For composed items, break them down into their sub-items. Focus on the raw items only, not the composed items themselves.
For each raw item, formulate a specific question to verify its compliance with the requirements outlined in the document. The question should be in the format: "Is [item information] compliant with the requirements?"
When generating each question, include all relevant information about the item so that the question can be answered without needing to refer back to the items table. This is important because the team verifying the items will not have access to the table.
Before providing the final questions, write out your thought process and reasoning inside <scratchpad> tags. Explain how you extracted the raw items and formulated each question.
Finally, output the generated questions inside <questions> tags, with each question on a separate line.

Remember, the goal is to create specific, informative questions for each raw item to verify compliance with the requirements outlined in the document. Make sure to provide all necessary context within the questions themselves.
"""
# answer in the language of the question only 

DOCUMENT_CONTEXT = """
The document is a list of specificity for a pastry product, every ingredient listed must be verified to be accepted by the Coup de Pates company.
Extract the individual raw ingredients from the ingredients table. For composed ingredients, break them down into their sub-ingredients. Focus on the raw ingredients only, not the composed ingredients themselves.
When generating each question, include all relevant information about the ingredient so that the question can be answered without needing to refer back to the ingredients table. This is important because the team verifying the ingredients will not have access to the table.
Look for the most detail in each ingredient, such as the labels (RSPCO, élevés en cage), do not add the country it is from.
Do not ask for an ingredient that is not raw, only raw ingredients are to be verified such as sugar, additifs, oil, colorants, etc.

The questions must be specific to a unique ingredient at each time.
The question will be asked directly to the "Charte Qualité" team, they won't have access to the provided document.
"""



class QuestionGenerator:
    def __init__(self, document_context = None):
        self.generic_prompt = GENERIC_PROMPT
        self.document_context = document_context if document_context else DOCUMENT_CONTEXT

    def table_to_text(self, df):
        text_rows = []
        for _, row in df.iterrows():
            row_text = " | ".join(str(value) for value in row.values if pd.notna(value))
            if row_text:
                text_rows.append("|" + row_text + "|")
        return "\n".join(text_rows)

    def generate_questions(self, xlsx_path: Path, tab_name: str, language_verification: bool = False):
        xls = pd.ExcelFile(xlsx_path)
        sheets = pd.read_excel(xls, tab_name)

        target_text = self.table_to_text(sheets)

        print("Generating Questions ...")

        prompt = PromptTemplate(
            template=self.generic_prompt,
            input_variables=["DOCUMENT", "DOCUMENT_CONTEXT"]
        )

        llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        llm_chain = prompt | llm

        questions = llm_chain.invoke({"DOCUMENT": target_text, "DOCUMENT_CONTEXT": self.document_context})

        soup = BeautifulSoup(str(questions.content), 'html.parser')
        questions_content = soup.find('questions').text  # type: ignore

        if language_verification:
            print("Verifying language and translating questions ...")
            llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
            prompt = PromptTemplate(
                template="""Traduit ces questions en francais : {questions} 
                
                Renvois un une liste avec les questions directement : """,
                input_variables=["questions"],
            )
            llm_chain = prompt | llm
            questions = llm_chain.invoke({"questions": questions_content})
            return questions.content


        return questions_content










