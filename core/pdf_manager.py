# pdf_editor/core/pdf_manager.py

import fitz  # PyMuPDF
from PIL import Image
import os


class PDFManager:
    def __init__(self):
        self.doc = None   # fitz.Document
        self.path = None
        self.current_page_index = 0

    def open_pdf(self, path: str):
        """Abre um PDF e reseta o índice de página."""
        self.close()
        self.doc = fitz.open(path)
        self.path = path
        self.current_page_index = 0

    def close(self):
        if self.doc is not None:
            self.doc.close()
        self.doc = None
        self.path = None
        self.current_page_index = 0

    def page_count(self) -> int:
        if self.doc is None:
            return 0
        return len(self.doc)

    def get_current_page_index(self) -> int:
        return self.current_page_index

    def go_to_page(self, index: int):
        if self.doc is None:
            return
        if 0 <= index < len(self.doc):
            self.current_page_index = index

    def next_page(self):
        if self.doc is None:
            return
        if self.current_page_index < len(self.doc) - 1:
            self.current_page_index += 1

    def prev_page(self):
        if self.doc is None:
            return
        if self.current_page_index > 0:
            self.current_page_index -= 1

    def render_current_page_image(self, zoom: float = 1.8) -> Image.Image:
        """Retorna a página atual como PIL.Image."""
        if self.doc is None:
            raise RuntimeError("Nenhum documento aberto.")

        page = self.doc.load_page(self.current_page_index)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img

    def extract_page_as_image(self, page_index: int, path: str, zoom: float = 2.0):
        """Exporta uma página específica como imagem PNG/JPEG."""
        if self.doc is None:
            raise RuntimeError("Nenhum documento aberto.")

        if not (0 <= page_index < len(self.doc)):
            raise IndexError("Índice de página inválido.")

        page = self.doc.load_page(page_index)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        ext = os.path.splitext(path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            fmt = "JPEG"
        else:
            fmt = "PNG"

        img.save(path, format=fmt)

    def extract_current_page_as_image(self, path: str, zoom: float = 2.0):
        """Exporta a página atual como imagem (atalho)."""
        if self.doc is None:
            raise RuntimeError("Nenhum documento aberto.")
        self.extract_page_as_image(self.current_page_index, path, zoom=zoom)

    def extract_text(self) -> str:
        """Extrai todo o texto do PDF como uma string."""
        if self.doc is None:
            raise RuntimeError("Nenhum documento aberto.")

        texts = []
        for page in self.doc:
            texts.append(page.get_text())
        return "\n".join(texts)

    def extract_text_page(self, page_index: int) -> str:
        """Extrai texto de uma página específica."""
        if self.doc is None:
            raise RuntimeError("Nenhum documento aberto.")
        if not (0 <= page_index < len(self.doc)):
            raise IndexError("Índice de página inválido.")

        page = self.doc.load_page(page_index)
        return page.get_text()
