from pathlib import Path

import pypdfium2 as pdfium


def test_pdfium():
    # scanned pdf
    p = Path("./tests/pdf/mlbook.pdf")
    document = pdfium.PdfDocument(p)

    objs = []
    for page in document:
        for obj in page.get_objects():
            objs.append(obj)

    document.close()
