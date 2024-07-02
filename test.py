from megaparse.Converter import MegaParse

megaparse = MegaParse(file_path="megaparse/tests/input_tests/MegaFake_report.pdf")
element = megaparse.load()
print("ok")
#megaparse.save_md(megaparse.convert(), "./multiplications.md")
