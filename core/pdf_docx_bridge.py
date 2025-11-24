# pdf_editor/core/pdf_docx_bridge.py

import os
from pdf2docx import Converter
from docx2pdf import convert as docx_to_pdf_convert


def pdf_to_docx(pdf_path: str, docx_path: str):
    """
    Converte um PDF em DOCX.
    """
    cv = Converter(pdf_path)
    try:
        cv.convert(docx_path)
    finally:
        cv.close()


def docx_to_pdf(docx_path: str, pdf_path: str = None):
    """
    Converte DOCX para PDF.
    Se pdf_path for None, gera um PDF com o mesmo nome do DOCX.
    """
    if pdf_path is None:
        base, _ = os.path.splitext(docx_path)
        pdf_path = base + ".pdf"

    docx_to_pdf_convert(docx_path, pdf_path)
    return pdf_path
