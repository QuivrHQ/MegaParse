import os
from collections import Counter
from typing import LiteralString

class MarkdownProcessor:
    def __init__(self, md_result: str, strict: bool, remove_pagination: bool):
        self.md_result = md_result
        self.strict = strict
        self.remove_pagination = remove_pagination

    @staticmethod
    def clean(text: str) -> str:
        """Clean the input text by removing newlines, double asterisks, and trimming whitespace."""
        text = text.replace("\n", "")
        text = text.replace("**", "")
        text = text.strip()
        return text

    def split_into_pages(self) -> list:
        """Split the markdown result into pages using triple newlines as the delimiter."""
        return self.md_result.split("\n\n\n")

    @staticmethod
    def split_into_paragraphs(pages: list) -> list:
        """Split pages into paragraphs using double newlines as the delimiter."""
        return "\n\n".join(pages).split("\n\n")

    def remove_duplicates(self, paragraphs: list) -> tuple:
        """Remove duplicate paragraphs and identify unique and duplicate paragraphs."""
        unique_paragraphs = list(set([self.clean(paragraph) for paragraph in paragraphs]))
        duplicate_paragraphs = []
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            cleaned_paragraph = self.clean(paragraph)
            if cleaned_paragraph in unique_paragraphs:
                cleaned_paragraphs.append(paragraph)
                unique_paragraphs.remove(cleaned_paragraph)
            else:
                duplicate_paragraphs.append(paragraph)

        return cleaned_paragraphs, duplicate_paragraphs

    def identify_header_components(self, duplicate_paragraphs: list) -> dict:
        """Identify words in duplicate paragraphs that are likely header components."""
        header_components = list(set([self.clean(paragraph) for paragraph in duplicate_paragraphs]))
        header_components = " ".join(header_components).strip().split(" ")
        header_components_count = Counter(header_components)
        header_components_count = {k.replace(":", ""): v for k, v in header_components_count.items() if v > 1 and len(k) > 3}
        return header_components_count

    def remove_header_lines(self, paragraphs: list, header_components_count: dict) -> list:
        """Remove paragraphs that contain any of the header words or the word 'Page' if remove_pagination is true."""
        def should_remove(paragraph):
            if self.remove_pagination and "Page" in paragraph:
                return True
            return any(word in paragraph for word in header_components_count.keys())

        return [paragraph for paragraph in paragraphs if not should_remove(paragraph)]
    
    def merge_tables(self, md_content: str):
        md_content = md_content.replace("|\n\n|", "|\n|")
        return md_content

    def save_cleaned_result(self, cleaned_result: str, output_path: str):
        """Save the cleaned paragraphs to a markdown file."""
        with open(output_path, "w") as f:
            f.write(cleaned_result)

    def process(self):
        """Process the markdown result by removing duplicate paragraphs and headers."""
        pages = self.split_into_pages()
        paragraphs = self.split_into_paragraphs(pages)
        #other_pages_paragraphs = self.split_into_paragraphs(pages[1:])

        cleaned_paragraphs, duplicate_paragraphs = self.remove_duplicates(paragraphs)
        header_components_count = self.identify_header_components(duplicate_paragraphs)

        if self.strict:
            final_paragraphs = self.remove_header_lines(cleaned_paragraphs[5:], header_components_count)
            final_paragraphs = cleaned_paragraphs[:5] + final_paragraphs
        else:
            final_paragraphs = cleaned_paragraphs

        # Combine first page paragraphs with cleaned paragraphs from other pages
        all_paragraphs = final_paragraphs
        cleaned_result = "\n\n".join(all_paragraphs)

        cleaned_result = self.merge_tables(cleaned_result)
        return cleaned_result

