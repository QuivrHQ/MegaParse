from typing import Any, Callable, List, Optional

from megaparse.base_element import (
    BaseElementNodeParser,
    Element,
)
from llama_index.core.schema import BaseNode, TextNode, NodeRelationship
from llama_index.core.node_parser.relational.utils import md_to_df
import pandas as pd


class MarkdownElementNodeParser(BaseElementNodeParser):
    """Markdown element node parser.

    Splits a markdown document into Text Nodes and Index Nodes corresponding to embedded objects
    (e.g. tables).

    """

    @classmethod
    def class_name(cls) -> str:
        return "MarkdownElementNodeParser"

    def get_nodes_from_node(self, node: TextNode) -> List[BaseNode]:
        """Get nodes from node."""
        elements = self.extract_elements(
            node.get_content(),
            table_filters=[self.filter_table],
            node_id=node.id_,
        )
        #remove nodes that are exactly the same

        #table_elements = self.get_table_elements(elements)
        table_elements = elements

        # extract summaries over table elements
        self.extract_table_summaries(table_elements)
        # convert into nodes
        # will return a list of Nodes and Index Nodes
        nodes = self.get_nodes_from_elements(
            elements, node.metadata, ref_doc_text=node.get_content()
        )
        source_document = node.source_node or node.as_related_node_info()
        for n in nodes:
            n.relationships[NodeRelationship.SOURCE] = source_document
            n.metadata.update(node.metadata)
        return nodes

    def extract_elements(
        self,
        text: str,
        node_id: Optional[str] = None,
        table_filters: Optional[List[Callable]] = None,
        **kwargs: Any,
    ) -> List[Element]:
        # get node id for each node so that we can avoid using the same id for different nodes
        """Extract elements from text."""
        lines = text.split("\n")
        currentElement = None

        elements: List[Element] = []
        # Then parse the lines
        for i,line in enumerate(lines):
            if line == "\n":
                continue
            if line.startswith("```"):
                # check if this is the end of a code block
                if currentElement is not None and currentElement.type == "code":
                    elements.append(currentElement)
                    currentElement = None
                    # if there is some text after the ``` create a text element with it
                    if len(line) > 3:
                        elements.append(
                            Element(
                                id=f"id_{len(elements)}",
                                type="text",
                                element=line.lstrip("```"),
                            )
                        )

                elif line.count("```") == 2 and line[-3] != "`":
                    # check if inline code block (aka have a second ``` in line but not at the end)
                    if currentElement is not None:
                        elements.append(currentElement)
                    currentElement = Element(
                        id=f"id_{len(elements)}",
                        type="code",
                        element=line.lstrip("```"),
                    )
                elif currentElement is not None and currentElement.type == "text":
                    currentElement.element += "\n" + line
                else:
                    if currentElement is not None:
                        elements.append(currentElement)
                    currentElement = Element(
                        id=f"id_{len(elements)}", type="text", element=line
                    )

            elif currentElement is not None and currentElement.type == "code":
                currentElement.element += "\n" + line

            elif line.startswith("|"):
                if currentElement is not None and currentElement.type != "table":
                    if currentElement is not None:
                        elements.append(currentElement)
                    currentElement = Element(
                        id=f"id_{len(elements)}", type="table", element=line
                    )
                elif currentElement is not None:
                    currentElement.element += "\n" + line
                else:
                    currentElement = Element(
                        id=f"id_{len(elements)}", type="table", element=line
                    )
            elif line.startswith("#"):
                if currentElement is not None:
                    elements.append(currentElement)
                currentElement = Element(
                    id=f"id_{len(elements)}",
                    type="title",
                    element=line.lstrip("#"),
                    title_level=len(line) - len(line.lstrip("#")),
                )
            else:
                if currentElement is not None and currentElement.type != "text":
                    elements.append(currentElement)
                    currentElement = Element(
                        id=f"id_{len(elements)}", type="text", element=line
                    )
                elif currentElement is not None:
                    currentElement.element += "\n" + line
                else:
                    currentElement = Element(
                        id=f"id_{len(elements)}", type="text", element=line
                    )
        if currentElement is not None and currentElement.element != "": #Modified by Chloé
            elements.append(currentElement)

        for idx, element in enumerate(elements):
            if element.type == "table":
                should_keep = True
                perfect_table = True

                # verify that the table (markdown) have the same number of columns on each rows
                table_lines = element.element.split("\n")
                table_columns = [len(line.split("|")) for line in table_lines]
                # for the lines that have less columns than the first line, we will add empty columns
                # Modfied by Chloé
                for i, columns in enumerate(table_columns):
                    if columns < table_columns[0]:
                        table_lines[i] += " |" * (table_columns[0] - columns)
                        table_columns[i] = table_columns[0]

                element.element = "\n".join(table_lines)
                # if len(set(table_columns)) > 1:
                #     # if the table have different number of columns on each rows, it's not a perfect table
                #     # we will store the raw text for such tables instead of converting them to a dataframe
                #    
                    
                #     #perfect_table = False

                # verify that the table (markdown) have at least 2 rows
                if len(table_lines) < 2:
                    should_keep = False

                # apply the table filter, now only filter empty tables
                if should_keep and perfect_table and table_filters is not None:
                    should_keep = all(tf(element) for tf in table_filters)

                # if the element is a table, convert it to a dataframe
                if should_keep:
                    if perfect_table:
                        table_content = "|".join([el.strip() if el != '\n' else el for el in element.element.split("|")])
                        table = md_to_df(table_content)
                        

                        table = self.move_duplicates_to_end(table)


                        elements[idx] = Element(
                            id=f"id_{node_id}_{idx}" if node_id else f"id_{idx}",
                            type="table",
                            element=element.element,
                            table=table,
                        )
                    else:
                        # for non-perfect tables, we will store the raw text
                        # and give it a different type to differentiate it from perfect tables
                        elements[idx] = Element(
                            id=f"id_{node_id}_{idx}" if node_id else f"id_{idx}",
                            type="table_text",
                            element=element.element,
                            # table=table
                        )
                else:
                    elements[idx] = Element(
                        id=f"id_{node_id}_{idx}" if node_id else f"id_{idx}",
                        type="text",
                        element=element.element,
                    )
            else:
                # if the element is not a table, keep it as to text
                elements[idx] = Element(
                    id=f"id_{node_id}_{idx}" if node_id else f"id_{idx}",
                    type="text",
                    element=element.element,
                )

        # merge consecutive text elements together for now
        merged_elements: List[Element] = []
        for element in elements:
            if (
                len(merged_elements) > 0
                and element.type == "text"
                and merged_elements[-1].type == "text"
            ):
                merged_elements[-1].element += "\n" + element.element
            else:
                merged_elements.append(element)
        elements = merged_elements
        return merged_elements

    def move_duplicates_to_end(self, df: pd.DataFrame):
        dupe_cols = df.loc[:, df.columns.str.contains(r"\.\d+$")]

        if not dupe_cols.empty:
            
            original_cols = df.loc[:, ~df.columns.str.contains(r"\.\d+$")]

            n_repetition = set([col.split(".")[-1] for col in dupe_cols.columns])

            concat_df = original_cols

            for i in n_repetition:
                dupe_df = dupe_cols.filter(regex=r"\." + i + "$")
                dupe_df.columns = dupe_df.columns.str.replace(r"\.\d+$", "", regex=True)

                concat_df = pd.concat([concat_df, dupe_df,], axis=0)
        else:
            concat_df = df

        def contains_alnum(row):
            return row.astype(str).str.contains(r'[a-zA-Z0-9]').any()

        # Filter rows that contain letters or numbers
        concat_df = concat_df.map(lambda x: x.strip() if isinstance(x, str) else x)
        concat_df = concat_df[concat_df.apply(contains_alnum, axis=1)]
        concat_df = concat_df.apply(lambda col: col.map(lambda x: x.replace("**", "").replace("*", "") if isinstance(x, str) else x))
        concat_df = concat_df.reset_index(drop=True)
        return concat_df

    def filter_table(self, table_element: Any) -> bool:
        """Filter tables."""
        table_df = md_to_df(table_element.element)

        # check if table_df is not None, has more than one row, and more than one column
        return table_df is not None and not table_df.empty and len(table_df.columns) > 1
