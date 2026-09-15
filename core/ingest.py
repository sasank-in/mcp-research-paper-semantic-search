"""PDF ingestion built on LangChain loaders and splitters."""
import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core import config
from core.vectorstore import add_documents, delete_source


class NoExtractableText(ValueError):
    """Raised when a PDF yields no text.

    Almost always a scanned document: the pages are images, with no text
    layer for pypdf to read. Such a file needs OCR before it can be indexed.
    """


_splitter = RecursiveCharacterTextSplitter(
    chunk_size=config.CHUNK_SIZE,
    chunk_overlap=config.CHUNK_OVERLAP,
    length_function=len,
    separators=["\n\n", "\n", " ", ""],
)


def load_pdf(path: str | Path) -> list[Document]:
    """Load one PDF into per-page Documents tagged with its filename."""
    path = Path(path)
    docs = PyPDFLoader(str(path)).load()
    for doc in docs:
        doc.metadata["filename"] = path.name
        doc.metadata["source"] = str(path)
    return docs


def chunk(documents: list[Document]) -> list[Document]:
    """Split Documents into embedding-sized chunks."""
    return _splitter.split_documents(documents) if documents else []


def ingest_pdf(path: str | Path, replace: bool = True) -> dict:
    """Load, chunk, embed, and store a single PDF.

    With replace=True any existing chunks for the same filename are removed
    first, so re-ingesting a paper does not create duplicates.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    documents = load_pdf(path)
    if not documents:
        raise NoExtractableText(
            f"{path.name} could not be read as a PDF, or contains no pages."
        )

    chunks = chunk(documents)
    if not chunks:
        raise NoExtractableText(
            f"No text could be extracted from {path.name}. It has "
            f"{len(documents)} page(s) but no text layer, which means it is "
            f"most likely a scanned document. Run it through OCR "
            f"(e.g. ocrmypdf) and upload the result."
        )

    if replace:
        delete_source(path.name)

    stored = add_documents(chunks)
    return {
        "filename": path.name,
        "pages": len(documents),
        "chunks": stored,
    }


def ingest_directory(folder: str | Path | None = None) -> dict:
    """Ingest every PDF in a folder."""
    folder = Path(folder or config.PAPERS_DIR)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        return {"processed": [], "failed": [], "total_chunks": 0}

    processed, failed, total = [], [], 0
    for pdf in pdfs:
        try:
            result = ingest_pdf(pdf)
            processed.append(result)
            total += result["chunks"]
            print(f"  [ok] {result['filename']}: {result['chunks']} chunks")
        except Exception as exc:
            failed.append({"filename": pdf.name, "error": str(exc)})
            print(f"  [fail] {pdf.name}: {exc}")

    return {"processed": processed, "failed": failed, "total_chunks": total}
