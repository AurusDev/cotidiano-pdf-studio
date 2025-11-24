# pdf_editor/core/pdf_merge.py

from pypdf import PdfWriter, PdfReader


def merge_pdfs(input_paths, output_path):
    """Mescla uma lista de PDFs em um único arquivo."""
    writer = PdfWriter()

    for pdf_path in input_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
