from io import BytesIO
from pathlib import Path
import re
from typing import List

import fitz
import pandas as pd


SUPPORTED_EXTENSIONS = {"pdf", "txt", "csv", "xlsx", "xls"}


def read_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        return file.read()


def normalize_extracted_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_pdf_file(file_path: str) -> str:
    document = fitz.open(file_path)
    pages = []
    for page in document:
        text = page.get_text("text", sort=True).strip()
        if text:
            pages.append(text)
            continue

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            document.close()
            raise ValueError(
                "This PDF contains scanned pages. Install OCR dependencies with "
                "'.venv/bin/pip install -r requirements.txt' and install Tesseract OCR."
            ) from exc

        try:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            text = pytesseract.image_to_string(image).strip()
        except Exception as exc:
            document.close()
            raise ValueError(f"OCR failed while reading PDF: {exc}") from exc
        if text:
            pages.append(text)
    document.close()
    return normalize_extracted_text("\n\n".join(pages))


def read_excel_file(file_path: str) -> str:
    dataframe = pd.read_excel(file_path)
    return dataframe.to_string(index=False)


def read_csv_file(file_path: str) -> str:
    last_error = None
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            dataframe = pd.read_csv(file_path, encoding=encoding)
            return dataframe.to_string(index=False)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(f"Unable to decode CSV file with supported encodings: {last_error}") from last_error


def extract_document_text(file_path: str) -> str:
    extension = Path(file_path).suffix.lower().replace(".", "")

    if extension == "pdf":
        return read_pdf_file(file_path)
    if extension == "txt":
        return read_text_file(file_path)
    if extension == "csv":
        return read_csv_file(file_path)
    if extension in {"xls", "xlsx"}:
        return read_excel_file(file_path)

    raise ValueError(f"Unsupported document extension: {extension}")


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 80) -> List[str]:
    if not text:
        return []

    paragraphs = [p.strip() for p in text.replace("\r", "").split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: List[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) <= chunk_size:
            current = (current + "\n\n" + paragraph).strip()
        else:
            if current:
                chunks.append(current)
            current = paragraph[:chunk_size]
            if len(paragraph) > chunk_size:
                parts = [paragraph[i : i + chunk_size] for i in range(0, len(paragraph), chunk_size - chunk_overlap)]
                chunks.extend(part for part in parts if part)
                current = ""
    if current:
        chunks.append(current)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def build_chunks_from_file(file_path: str) -> List[str]:
    raw_text = extract_document_text(file_path)
    return chunk_text(raw_text)
