# Cotidiano PDF Studio

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
![Platform](https://img.shields.io/badge/Plataforma-Windows-0078D6?logo=windows)
[![License](https://img.shields.io/github/license/AurusDev/cotidiano-pdf-studio)](LICENSE)
[![Repo size](https://img.shields.io/github/repo-size/AurusDev/cotidiano-pdf-studio)](https://github.com/AurusDev/cotidiano-pdf-studio)
[![Last commit](https://img.shields.io/github/last-commit/AurusDev/cotidiano-pdf-studio)](https://github.com/AurusDev/cotidiano-pdf-studio/commits/main)
[![Downloads](https://img.shields.io/github/downloads/AurusDev/cotidiano-pdf-studio/total)](https://github.com/AurusDev/cotidiano-pdf-studio/releases)

---

## ⬇️ Download

👉 **Download recomendado (Windows – instalador .exe):**

[🚀 Baixar Cotidiano PDF Studio (Setup .exe)](https://github.com/AurusDev/cotidiano-pdf-studio/releases/download/v1.0.0/CotidianoPDFStudioSetup.exe)

> Se o link não funcionar ainda, veja a seção **“Publicando o setup nas Releases”** abaixo – você precisa subir o arquivo na aba *Releases* uma vez.

---

## ℹ️ Sobre o projeto

**Cotidiano PDF Studio** é um aplicativo desktop em Python para quem lida diariamente com PDFs e quer uma ferramenta simples, direta e visual para fazer edições rápidas sem depender de suítes pesadas.

O foco é o uso no dia a dia: alterar informações pontuais em documentos, mesclar PDFs, extrair páginas e textos, tudo com uma interface amigável construída em **CustomTkinter**.

---

## ✨ Funcionalidades

- 🖼 **Visualização de PDF em alta qualidade**
  - Página centralizada e redimensionada automaticamente
  - Navegação por páginas (anterior/próxima)

- ➕ **Mesclar PDFs**
  - Seleciona múltiplos PDFs e gera um documento único
  - Após mesclar:
    - o PDF resultante já é carregado no visualizador principal
    - abre uma janela de pré-visualização com **scroll vertical**, mostrando todas as páginas em sequência (principal + anexados)

- 🖼 **Extrair página como imagem**
  - Escolhe o número da página
  - Exporta como `.png` ou `.jpg`

- 📝 **Extrair texto do PDF**
  - Abre um modal com todo o texto extraído
  - Opção de salvar como `.txt`

- ✏️ **Modo editor interno de texto**
  - Ao ativar o modo editor:
    - Você dá **duplo clique** em qualquer linha do PDF
    - Uma **caixa de texto** aparece exatamente sobre a linha
    - Você pode:
      - editar o texto
      - **arrastar** a caixa (para reposicionar)
      - **redimensionar** puxando o canto inferior direito
    - Ao pressionar **Enter**:
      - a edição é aplicada **em tempo real** na visualização do PDF
      - o texto original é “apagado” visualmente e o novo é desenhado por cima
  - Barra de formatação:
    - Fonte (Arial, Times New Roman, Courier New)
    - Tamanho
    - Negrito / Itálico
    - Cor do texto

- 💾 **Salvar edição no PDF**
  - Quando estiver satisfeito com as alterações visuais:
    - clica em **Salvar edição no PDF**
    - o PDF original é carregado com PyMuPDF
    - para cada edição:
      - a área é pintada de branco
      - o novo texto é escrito na área correspondente
    - o resultado é salvo em um novo arquivo `.pdf`

---

## 🧱 Tecnologias usadas

- **Python 3.11+**
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** – UI moderna e dark mode
- **[PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)** – manipulação e renderização de PDFs
- **[Pillow](https://pillow.readthedocs.io/)** – manipulação de imagens
- **PyInstaller** – geração de executável
- **Inno Setup** – criação de instalador (setup)

---

## 📁 Estrutura do projeto

```text
pdf_editor/
├─ assets/
│   └─ codex_pdf.ico            # Ícone do aplicativo / instalador
├─ core/
│   ├─ pdf_manager.py           # Lógica de abertura, navegação e renderização de PDF
│   ├─ pdf_merge.py             # Funções de mesclagem de PDFs
│   └─ pdf_docx_bridge.py       # (se usado) ponte para conversão/editors externos
├─ ui/
│   ├─ __init__.py
│   └─ main_window.py           # Interface principal + modo editor interno
├─ main.py                      # Ponto de entrada do aplicativo
├─ requirements.txt             # Dependências do projeto
└─ installer_cotidiano.iss      # Script do Inno Setup (opcional)
