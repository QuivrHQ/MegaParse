from Converter import MegaParse

megaparse = MegaParse(file_path="./test.pdf")
megaparse.save_md(megaparse.convert(), "./test.md")
