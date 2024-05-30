from Converter import MegaParse

megaparse = MegaParse(file_path="./multiplications.pdf")
megaparse.save_md(megaparse.convert(), "./multiplications.md")
