# pdf_editor/ui/main_window.py

import os
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser

import customtkinter as ctk
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

from core.pdf_manager import PDFManager
from core.pdf_merge import merge_pdfs


def hex_to_rgb01(hex_color: str):
    """Converte '#RRGGBB' para (r, g, b) em 0-1 (usado pelo PyMuPDF)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return 0, 0, 0
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return r, g, b


FONT_MAP = {
    "Arial": "helv",
    "Times New Roman": "tiro",
    "Courier New": "cour",
}


class PDFEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração básica
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Cotidiano PDF Studio")
        self.geometry("1200x700")
        self.minsize(900, 600)

        # Estado do PDF / imagem
        self.pdf_manager = PDFManager()
        self.current_page_image = None  # CTkImage
        self.display_img_size = None    # (w, h) exibida
        self.full_img_size = None       # (w, h) original
        self.display_zoom = 1.8         # zoom usado ao renderizar

        # Estado de edição
        # page_index -> [ { "pdf_rect":(x0,y0,x1,y1), "text":str, "widget":CTkTextbox|None, ... } ]
        self.text_overlays = {}
        self.active_overlay = None
        self.editor_mode = False

        # Estado da formatação
        self.editor_font_family = tk.StringVar(value="Arial")
        self.editor_font_size = tk.IntVar(value=12)
        self.editor_bold = tk.BooleanVar(value=False)
        self.editor_italic = tk.BooleanVar(value=False)
        self.editor_underline = tk.BooleanVar(value=False)  # não usado no PDF ainda
        self.editor_color = "#000000"

        # Interface
        self._build_layout()

    # =============================
    # Layout
    # =============================

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(12, weight=1)

        title_label = ctk.CTkLabel(
            self.sidebar,
            text="Códex PDF Studio",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="Ferramentas",
            font=ctk.CTkFont(size=14)
        )
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # Botões principais
        ctk.CTkButton(
            self.sidebar,
            text="📂 Abrir PDF",
            command=self.open_pdf_dialog
        ).grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkButton(
            self.sidebar,
            text="➕ Mesclar PDFs",
            command=self.merge_pdfs_dialog
        ).grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkButton(
            self.sidebar,
            text="🖼️ Extrair página como imagem",
            command=self.extract_page_as_image_dialog
        ).grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkButton(
            self.sidebar,
            text="📝 Extrair texto do PDF",
            command=self.extract_text_dialog
        ).grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        # Modo editor híbrido
        ctk.CTkLabel(
            self.sidebar,
            text="Modo editor interno",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")

        self.editor_mode_btn = ctk.CTkButton(
            self.sidebar,
            text="✏️ Ativar modo editor",
            command=self.toggle_editor_mode
        )
        self.editor_mode_btn.grid(row=7, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkButton(
            self.sidebar,
            text="💾 Salvar edição no PDF",
            command=self.apply_overlays_to_pdf
        ).grid(row=8, column=0, padx=20, pady=5, sticky="ew")

        # Navegação de página
        nav_frame = ctk.CTkFrame(self.sidebar)
        nav_frame.grid(row=11, column=0, padx=20, pady=20, sticky="ew")
        nav_frame.grid_columnconfigure((0, 2), weight=1)

        ctk.CTkButton(
            nav_frame, text="⬅", width=10, command=self.prev_page
        ).grid(row=0, column=0, padx=5, pady=5)

        self.page_label = ctk.CTkLabel(
            nav_frame, text="Página -/-", font=ctk.CTkFont(size=12)
        )
        self.page_label.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkButton(
            nav_frame, text="➡", width=10, command=self.next_page
        ).grid(row=0, column=2, padx=5, pady=5)

        # Área de preview
        self.preview_frame = ctk.CTkFrame(self, corner_radius=0)
        self.preview_frame.grid(row=0, column=1, sticky="nsew")
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        # Toolbar do editor (começa oculta)
        self.editor_toolbar = ctk.CTkFrame(self.preview_frame)
        self._build_editor_toolbar()
        self.editor_toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.editor_toolbar.grid_remove()

        # Label de preview da página
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Abra um PDF para começar",
            font=ctk.CTkFont(size=16)
        )
        self.preview_label.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # Resize + double click
        self.preview_frame.bind("<Configure>", self.on_preview_resize)
        self.preview_label.bind("<Double-Button-1>", self.on_preview_double_click)

    def _build_editor_toolbar(self):
        """Barra de ferramentas para formatação de texto."""
        self.editor_toolbar.grid_columnconfigure(6, weight=1)

        font_label = ctk.CTkLabel(self.editor_toolbar, text="Fonte:")
        font_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")

        font_combo = ctk.CTkComboBox(
            self.editor_toolbar,
            values=["Arial", "Times New Roman", "Courier New"],
            variable=self.editor_font_family,
            command=lambda _: self.update_active_overlay_style()
        )
        font_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        size_label = ctk.CTkLabel(self.editor_toolbar, text="Tamanho:")
        size_label.grid(row=0, column=2, padx=(15, 5), pady=5, sticky="w")

        size_combo = ctk.CTkComboBox(
            self.editor_toolbar,
            values=[str(s) for s in (8, 9, 10, 11, 12, 14, 16, 18, 20, 24)],
            command=self._on_size_change
        )
        size_combo.set(str(self.editor_font_size.get()))
        size_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        bold_btn = ctk.CTkButton(
            self.editor_toolbar,
            text="B",
            width=24,
            command=self.toggle_bold
        )
        bold_btn.grid(row=0, column=4, padx=(15, 2), pady=5, sticky="w")

        italic_btn = ctk.CTkButton(
            self.editor_toolbar,
            text="I",
            width=24,
            command=self.toggle_italic
        )
        italic_btn.grid(row=0, column=5, padx=2, pady=5, sticky="w")

        underline_btn = ctk.CTkButton(
            self.editor_toolbar,
            text="U",
            width=24,
            command=self.toggle_underline
        )
        underline_btn.grid(row=0, column=6, padx=2, pady=5, sticky="w")

        color_btn = ctk.CTkButton(
            self.editor_toolbar,
            text="Cor",
            width=40,
            command=self.choose_color
        )
        color_btn.grid(row=0, column=7, padx=(15, 0), pady=5, sticky="w")

    # =============================
    # Helpers de layout / overlays
    # =============================

    def _get_image_display_geometry(self):
        """Retorna (label_x, label_y, img_left, img_top, img_w, img_h)."""
        if self.display_img_size is None:
            return 0, 0, 0, 0, 0, 0

        label = self.preview_label
        img_w, img_h = self.display_img_size
        label_w = label.winfo_width()
        label_h = label.winfo_height()

        img_left = max((label_w - img_w) / 2, 0)
        img_top = max((label_h - img_h) / 2, 0)

        label_x = label.winfo_x()
        label_y = label.winfo_y()

        return label_x, label_y, img_left, img_top, img_w, img_h

    def clear_overlays(self):
        """Remove todas as caixas de texto da interface e memória."""
        for overlays in self.text_overlays.values():
            for ov in overlays:
                widget = ov.get("widget")
                if widget is not None:
                    try:
                        widget.destroy()
                    except Exception:
                        pass
        self.text_overlays.clear()
        self.active_overlay = None

    def update_overlay_positions(self):
        """Reposiciona / mostra as caixas da página atual (esconde as outras)."""
        for overlays in self.text_overlays.values():
            for ov in overlays:
                widget = ov.get("widget")
                if widget:
                    widget.place_forget()

        if not self.editor_mode:
            return
        if self.pdf_manager.doc is None:
            return
        if self.display_img_size is None or self.full_img_size is None:
            return

        page_index = self.pdf_manager.get_current_page_index()
        page_overlays = self.text_overlays.get(page_index, [])
        if not page_overlays:
            return

        label_x, label_y, img_left, img_top, img_w, img_h = self._get_image_display_geometry()
        full_w, _ = self.full_img_size
        if img_w <= 0 or full_w <= 0:
            return

        scale = full_w / img_w
        page = self.pdf_manager.doc.load_page(page_index)
        rect_page = page.rect

        for ov in page_overlays:
            widget = ov.get("widget")
            if not widget:
                continue

            x0, y0, x1, y1 = ov["pdf_rect"]

            x0_full = (x0 - rect_page.x0) * self.display_zoom
            y0_full = (y0 - rect_page.y0) * self.display_zoom
            x1_full = (x1 - rect_page.x0) * self.display_zoom
            y1_full = (y1 - rect_page.y0) * self.display_zoom

            x0_disp = x0_full / scale
            y0_disp = y0_full / scale
            w_disp = (x1_full - x0_full) / scale
            h_disp = (y1_full - y0_full) / scale

            overlay_x = label_x + img_left + x0_disp
            overlay_y = label_y + img_top + y0_disp

            widget.configure(width=int(w_disp), height=int(h_disp))
            widget.place(x=int(overlay_x), y=int(overlay_y))

    # =============================
    # Ações principais
    # =============================

    def open_pdf_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if not file_path:
            return

        try:
            self.clear_overlays()
            self.pdf_manager.open_pdf(file_path)
            self.show_current_page()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o PDF.\n\n{e}")

    def show_current_page(self):
        """Renderiza a página + aplica as edições visuais (preview)."""
        if self.pdf_manager.doc is None:
            return

        try:
            self.display_zoom = 1.8
            img_full = self.pdf_manager.render_current_page_image(zoom=self.display_zoom)
            self.full_img_size = img_full.size

            frame_width = self.preview_frame.winfo_width()
            frame_height = self.preview_frame.winfo_height()

            img = img_full.copy()
            if frame_width > 80 and frame_height > 80:
                img.thumbnail((frame_width - 80, frame_height - 80))

            self.display_img_size = img.size

            page_idx = self.pdf_manager.get_current_page_index()
            page = self.pdf_manager.doc.load_page(page_idx)
            rect_page = page.rect
            full_w, _ = self.full_img_size
            disp_w, _ = self.display_img_size
            scale = full_w / disp_w if disp_w > 0 else 1.0

            overlays = self.text_overlays.get(page_idx, [])
            if overlays:
                draw = ImageDraw.Draw(img)
                try:
                    font_pil = ImageFont.truetype("arial.ttf", self.editor_font_size.get())
                except Exception:
                    font_pil = ImageFont.load_default()

                for ov in overlays:
                    text = ov.get("text")
                    if not text:
                        continue

                    x0, y0, x1, y1 = ov["pdf_rect"]

                    x0_full = (x0 - rect_page.x0) * self.display_zoom
                    y0_full = (y0 - rect_page.y0) * self.display_zoom
                    x1_full = (x1 - rect_page.x0) * self.display_zoom
                    y1_full = (y1 - rect_page.y0) * self.display_zoom

                    x0_disp = x0_full / scale
                    y0_disp = y0_full / scale
                    x1_disp = x1_full / scale
                    y1_disp = y1_full / scale

                    draw.rectangle([x0_disp, y0_disp, x1_disp, y1_disp], fill="white")
                    draw.text(
                        (x0_disp + 2, y0_disp + 2),
                        text,
                        fill=self.editor_color,
                        font=font_pil,
                    )

            self.current_page_image = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=img.size
            )
            self.preview_label.configure(image=self.current_page_image, text="")
            self.preview_label.image = self.current_page_image

            total = self.pdf_manager.page_count()
            self.page_label.configure(text=f"Página {page_idx + 1}/{total}")

            self.update_overlay_positions()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao renderizar página.\n\n{e}")

    # ---------- NOVO: visualização com scroll do PDF mesclado ----------

    def show_merged_preview(self, merged_path: str):
        """Abre uma janela com scroll vertical mostrando TODAS as páginas do PDF mesclado."""
        try:
            doc = fitz.open(merged_path)
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Não foi possível abrir o PDF mesclado para visualização.\n\n{e}"
            )
            return

        win = ctk.CTkToplevel(self)
        win.title(f"Pré-visualização do PDF mesclado - {os.path.basename(merged_path)}")
        win.geometry("900x700")

        info_label = ctk.CTkLabel(
            win,
            text=f"PDF mesclado: {os.path.basename(merged_path)}\n"
                 f"Use a barra de rolagem para ver todas as páginas.",
            font=ctk.CTkFont(size=14, weight="bold"),
            justify="center"
        )
        info_label.pack(padx=10, pady=(10, 5))

        scroll = ctk.CTkScrollableFrame(win, width=850, height=600)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        num_pages = doc.page_count
        for i in range(num_pages):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Redimensiona para caber na largura do frame, se necessário
            max_width = 800
            if img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            cimg = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            page_label = ctk.CTkLabel(scroll, image=cimg, text=f"Página {i+1}")
            page_label.image = cimg
            page_label.pack(pady=(5, 20))

        doc.close()

    # ---------- /NOVO visualização mesclado ----------

    def merge_pdfs_dialog(self):
        """Mescla PDFs e abre uma visualização com scroll do resultado."""
        file_paths = filedialog.askopenfilenames(
            title="Selecione os PDFs para mesclar (o PDF atual será o primeiro, se incluído)",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if not file_paths:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
            title="Salvar PDF mesclado como"
        )
        if not save_path:
            return

        try:
            merge_pdfs(file_paths, save_path)
            messagebox.showinfo(
                "Sucesso",
                f"PDFs mesclados com sucesso!\n\nArquivo salvo em:\n{save_path}"
            )

            # Atualiza visualização principal para o PDF mesclado
            self.clear_overlays()
            self.pdf_manager.open_pdf(save_path)
            self.show_current_page()

            # E abre uma janela extra com scroll, mostrando tudo em sequência
            self.show_merged_preview(save_path)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao mesclar PDFs.\n\n{e}")

    # =============================
    # Outras funcionalidades
    # =============================

    def extract_page_as_image_dialog(self):
        if self.pdf_manager.doc is None:
            messagebox.showwarning("Atenção", "Nenhum PDF aberto.")
            return

        total = self.pdf_manager.page_count()
        dialog = ctk.CTkInputDialog(
            title="Escolher página",
            text=f"Digite o número da página para exportar (1 - {total}):"
        )
        value = dialog.get_input()
        if value is None:
            return

        try:
            page_num = int(value)
        except ValueError:
            messagebox.showerror("Erro", "Número de página inválido.")
            return

        if not (1 <= page_num <= total):
            messagebox.showerror("Erro", "Número de página fora do intervalo.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg")],
            title="Salvar página como imagem"
        )
        if not save_path:
            return

        try:
            self.pdf_manager.extract_page_as_image(page_num - 1, save_path, zoom=2.0)
            messagebox.showinfo(
                "Sucesso",
                f"Página {page_num} salva como imagem com sucesso."
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar imagem.\n\n{e}")

    def extract_text_dialog(self):
        if self.pdf_manager.doc is None:
            messagebox.showwarning("Atenção", "Nenhum PDF aberto.")
            return

        try:
            text = self.pdf_manager.extract_text()

            text_window = ctk.CTkToplevel(self)
            text_window.title("Texto extraído do PDF")
            text_window.geometry("800x600")

            text_window.transient(self)
            text_window.grab_set()
            text_window.lift()
            text_window.focus_force()
            text_window.attributes("-topmost", True)
            text_window.after(200, lambda: text_window.attributes("-topmost", False))

            text_box = ctk.CTkTextbox(text_window, wrap="word")
            text_box.pack(fill="both", expand=True, padx=10, pady=10)
            text_box.insert("1.0", text)

            def save_txt():
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Arquivo de texto", "*.txt")],
                    title="Salvar texto como"
                )
                if not save_path:
                    return
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text)
                messagebox.showinfo("Sucesso", "Texto salvo com sucesso.")

            save_btn = ctk.CTkButton(
                text_window,
                text="Salvar como .txt",
                command=save_txt
            )
            save_btn.pack(pady=10)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao extrair texto.\n\n{e}")

    # =============================
    # Modo editor híbrido (drag + resize)
    # =============================

    def toggle_editor_mode(self):
        self.editor_mode = not self.editor_mode
        if self.editor_mode:
            self.editor_toolbar.grid()
            self.editor_mode_btn.configure(text="✏️ Desativar modo editor")
        else:
            self.editor_toolbar.grid_remove()
            self.editor_mode_btn.configure(text="✏️ Ativar modo editor")
        self.update_overlay_positions()

    def on_preview_double_click(self, event):
        """Cria caixa de edição na linha/área clicada (arrastável e redimensionável)."""
        if not self.editor_mode:
            return
        if self.pdf_manager.doc is None:
            return
        if self.display_img_size is None:
            return

        page_index = self.pdf_manager.get_current_page_index()
        page = self.pdf_manager.doc.load_page(page_index)
        rect_page = page.rect

        label_x, label_y, img_left, img_top, img_w, img_h = self._get_image_display_geometry()
        img_disp_w, img_disp_h = self.display_img_size
        if img_disp_w <= 0 or img_disp_h <= 0:
            return

        click_x = event.x
        click_y = event.y

        x_in_disp = click_x - img_left
        y_in_disp = click_y - img_top

        x_in_disp = max(0, min(img_disp_w - 1, x_in_disp))
        y_in_disp = max(0, min(img_disp_h - 1, y_in_disp))

        full_w, full_h = self.full_img_size or self.display_img_size
        zoom = self.display_zoom or 1.0
        scale = full_w / img_disp_w if img_disp_w != 0 else 1.0

        x_full = x_in_disp * scale
        y_full = y_in_disp * scale

        x_pdf = rect_page.x0 + x_full / zoom
        y_pdf = rect_page.y0 + y_full / zoom

        words = page.get_text("words")

        if words:
            chosen = None
            for w in words:
                x0, y0, x1, y1, text, b_no, l_no, w_no = w
                if x0 <= x_pdf <= x1 and y0 <= y_pdf <= y1:
                    chosen = w
                    break

            if chosen is None:
                best_dist = float("inf")
                for w in words:
                    x0, y0, x1, y1, text, b_no, l_no, w_no = w
                    cx = (x0 + x1) / 2
                    cy = (y0 + y1) / 2
                    d = (cx - x_pdf) ** 2 + (cy - y_pdf) ** 2
                    if d < best_dist:
                        best_dist = d
                        chosen = w

            x0_c, y0_c, x1_c, y1_c, text_c, block_no, line_no, _ = chosen

            line_words = [
                w for w in words
                if w[5] == block_no and w[6] == line_no
            ]
            line_words.sort(key=lambda w: w[7])

            line_text = " ".join(w[4] for w in line_words)
            x0_line = min(w[0] for w in line_words)
            y0_line = min(w[1] for w in line_words)
            x1_line = max(w[2] for w in line_words)
            y1_line = max(w[3] for w in line_words)
        else:
            line_text = ""
            largura_pdf = rect_page.width * 0.3
            altura_pdf = rect_page.height * 0.02
            x0_line = x_pdf
            y0_line = y_pdf
            x1_line = x_pdf + largura_pdf
            y1_line = y_pdf + altura_pdf

        pdf_rect = (x0_line, y0_line, x1_line, y1_line)

        x0_full = (x0_line - rect_page.x0) * zoom
        y0_full = (y0_line - rect_page.y0) * zoom
        x1_full = (x1_line - rect_page.x0) * zoom
        y1_full = (y1_line - rect_page.y0) * zoom

        x0_disp = x0_full / scale
        y0_disp = y0_full / scale
        w_disp = max(30, (x1_full - x0_full) / scale)
        h_disp = max(20, (y1_full - y0_full) / scale)

        overlay_x = label_x + img_left + x0_disp
        overlay_y = label_y + img_top + y0_disp

        text_box = ctk.CTkTextbox(
            self.preview_frame,
            fg_color="#ffffff",
            width=int(w_disp),
            height=int(h_disp),
        )
        text_box.place(x=int(overlay_x), y=int(overlay_y))
        if line_text:
            text_box.insert("1.0", line_text)
        text_box.focus()

        overlay = {
            "page_index": page_index,
            "pdf_rect": pdf_rect,
            "text": line_text,
            "widget": text_box,
            "dragging": False,
            "resizing": False,
            "drag_offset_x": 0,
            "drag_offset_y": 0,
        }

        def _on_click(_event, ov=overlay):
            self.active_overlay = ov

        text_box.bind("<Button-1>", _on_click)

        def _on_press(e, ov=overlay):
            w = ov["widget"].winfo_width()
            h = ov["widget"].winfo_height()
            border = 10
            if e.x >= w - border and e.y >= h - border:
                ov["resizing"] = True
                ov["dragging"] = False
            else:
                ov["dragging"] = True
                ov["resizing"] = False
                ov["drag_offset_x"] = e.x
                ov["drag_offset_y"] = e.y

        def _on_motion(e, ov=overlay):
            widget = ov["widget"]
            if widget is None:
                return
            if ov["dragging"]:
                new_x = widget.winfo_x() + (e.x - ov["drag_offset_x"])
                new_y = widget.winfo_y() + (e.y - ov["drag_offset_y"])
                widget.place(x=new_x, y=new_y)
            elif ov["resizing"]:
                new_w = max(30, e.x)
                new_h = max(20, e.y)
                widget.configure(width=int(new_w), height=int(new_h))

        def _on_release(e, ov=overlay):
            ov["dragging"] = False
            ov["resizing"] = False

        text_box.bind("<ButtonPress-1>", _on_press)
        text_box.bind("<B1-Motion>", _on_motion)
        text_box.bind("<ButtonRelease-1>", _on_release)

        def _on_return(ev, ov=overlay):
            self.commit_overlay(ov)
            return "break"

        text_box.bind("<Return>", _on_return)

        self.text_overlays.setdefault(page_index, []).append(overlay)
        self.active_overlay = overlay
        self.apply_format_to_overlay(overlay)

    def commit_overlay(self, overlay):
        """Confirma edição: usa posição/tamanho ATUAL da caixa para recalcular a área no PDF."""
        widget = overlay.get("widget")
        if widget is None:
            return

        text = widget.get("1.0", "end-1c").strip()
        overlay["text"] = text

        page_index = overlay["page_index"]
        page = self.pdf_manager.doc.load_page(page_index)
        rect_page = page.rect

        label_x, label_y, img_left, img_top, img_w, img_h = self._get_image_display_geometry()
        full_w, full_h = self.full_img_size or self.display_img_size
        zoom = self.display_zoom or 1.0
        disp_w, disp_h = self.display_img_size
        scale = full_w / disp_w if disp_w > 0 else 1.0

        widget_x = widget.winfo_x()
        widget_y = widget.winfo_y()
        widget_w = widget.winfo_width()
        widget_h = widget.winfo_height()

        x_disp = widget_x - (label_x + img_left)
        y_disp = widget_y - (label_y + img_top)

        x_disp = max(0, min(img_w - 1, x_disp))
        y_disp = max(0, min(img_h - 1, y_disp))

        w_disp = min(widget_w, img_w - x_disp)
        h_disp = min(widget_h, img_h - y_disp)

        x_full = x_disp * scale
        y_full = y_disp * scale
        w_full = w_disp * scale
        h_full = h_disp * scale

        x_pdf = rect_page.x0 + x_full / zoom
        y_pdf = rect_page.y0 + y_full / zoom
        x1_pdf = x_pdf + w_full / zoom
        y1_pdf = y_pdf + h_full / zoom

        overlay["pdf_rect"] = (x_pdf, y_pdf, x1_pdf, y1_pdf)

        try:
            widget.destroy()
        except Exception:
            pass
        overlay["widget"] = None
        self.active_overlay = None

        self.show_current_page()

    def apply_format_to_overlay(self, overlay):
        widget = overlay.get("widget")
        if widget is None:
            return

        style_parts = []
        if self.editor_bold.get():
            style_parts.append("bold")
        if self.editor_italic.get():
            style_parts.append("italic")

        style = " ".join(style_parts) if style_parts else "normal"
        font_tuple = (self.editor_font_family.get(), self.editor_font_size.get(), style)
        widget.configure(font=font_tuple, text_color=self.editor_color, fg_color="#ffffff")

    def update_active_overlay_style(self):
        if self.active_overlay is not None:
            self.apply_format_to_overlay(self.active_overlay)

    def _on_size_change(self, value: str):
        try:
            self.editor_font_size.set(int(value))
        except ValueError:
            return
        self.update_active_overlay_style()

    def toggle_bold(self):
        self.editor_bold.set(not self.editor_bold.get())
        self.update_active_overlay_style()

    def toggle_italic(self):
        self.editor_italic.set(not self.editor_italic.get())
        self.update_active_overlay_style()

    def toggle_underline(self):
        self.editor_underline.set(not self.editor_underline.get())

    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.editor_color)[1]
        if color:
            self.editor_color = color
            self.update_active_overlay_style()

    def apply_overlays_to_pdf(self):
        if self.pdf_manager.doc is None:
            messagebox.showwarning("Atenção", "Nenhum PDF aberto.")
            return

        if not any(self.text_overlays.values()):
            messagebox.showinfo("Info", "Nenhuma edição para aplicar.")
            return

        save_pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
            title="Salvar PDF editado como"
        )
        if not save_pdf_path:
            return

        try:
            doc = self.pdf_manager.doc
            rgb_color = hex_to_rgb01(self.editor_color)
            font_name = FONT_MAP.get(self.editor_font_family.get(), "helv")
            font_size = self.editor_font_size.get()

            for page_index, overlays in self.text_overlays.items():
                page = doc.load_page(page_index)

                for ov in overlays:
                    text = ov.get("text", "").strip()
                    if not text:
                        continue

                    x0, y0, x1, y1 = ov["pdf_rect"]
                    rect_overlay = fitz.Rect(x0, y0, x1, y1)

                    page.draw_rect(rect_overlay, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_textbox(
                        rect_overlay,
                        text,
                        fontsize=font_size,
                        fontname=font_name,
                        color=rgb_color,
                        align=0,
                    )

            doc.save(save_pdf_path)
            messagebox.showinfo(
                "Sucesso",
                f"Edições aplicadas e PDF salvo em:\n{save_pdf_path}"
            )

            self.clear_overlays()
            self.pdf_manager.open_pdf(save_pdf_path)
            self.show_current_page()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao aplicar edições.\n\n{e}")

    # =============================
    # Navegação + resize
    # =============================

    def next_page(self):
        self.pdf_manager.next_page()
        self.show_current_page()

    def prev_page(self):
        self.pdf_manager.prev_page()
        self.show_current_page()

    def on_preview_resize(self, event):
        if self.pdf_manager.doc is None:
            return
        self.show_current_page()
