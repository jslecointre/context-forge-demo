import argparse
import json
import logging
import os
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path
import chromadb

# from docling.chunking import HybridChunker
# from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from langchain_chroma.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from langchain_ibm import WatsonxEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "timestamp": self.formatTime(record, self.datefmt),
                "name": record.name,
                "funcName": record.funcName,
                "level": record.levelname,
                "message": record.getMessage(),
                "filename": record.filename,
                "line": record.lineno,
            }
        )


def _setup_logger() -> logging.Logger:
    log_file = PROJECT_ROOT / "logs" / "cf_demo_backend_logs.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
    file_handler.setFormatter(JsonFormatter())

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JsonFormatter())

    lgr = logging.getLogger(__name__)
    lgr.setLevel(logging.INFO)
    lgr.addHandler(file_handler)
    lgr.addHandler(stream_handler)
    lgr.propagate = False
    return lgr


for _name in ("absl", "httpx", "mcp.client.sse", "root"):
    logging.getLogger(_name).setLevel(logging.ERROR)

logger = _setup_logger()

embeddings = WatsonxEmbeddings(
    model_id="intfloat/multilingual-e5-large",
    url=os.getenv("WATSONX_URL"),
    project_id=os.getenv("WATSONX_PROJECT_ID"),
)
# Configure the export type for Docling loader
# Options: ExportType.DOC_CHUNKS (pre-chunked by Docling) or ExportType.MARKDOWN (markdown export)
EXPORT_TYPE = ExportType.DOC_CHUNKS
# EXPORT_TYPE = ExportType.MARKDOWN
DB_DIR = f"./{os.getenv('VDB_DIR','store')}"

# Configure Docling pipeline options
pipeline_options = PdfPipelineOptions()
pipeline_options.allow_external_plugins = True

# Create a DocumentConverter with the pipeline options
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

# Mapping of PDF filenames to their source URLs
PDF_SOURCE_URLS = {
    "field-underwriting-manual-984e.pdf": "https://www.bmo.com/advisor/PDFs/field-underwriting-manual-984e.pdf",
    "iaa.pdf": "https://iaa.secureweb.inalco.com/cw//cw/-/media/documents-repository/individual-insurance-savings-and-retirement/individual-insurance/2019/06/dev004399.pdf",
}


def get_source_url(file_path: str) -> str:
    """Get the source URL for a PDF file path.

    Args:
        file_path: Local file path to the PDF.

    Returns:
        The source URL if mapped, otherwise the original file path.
    """
    filename = os.path.basename(file_path)
    return PDF_SOURCE_URLS.get(filename, file_path)


def download_pdf(pdf_name: str, dest_dir: str = "data") -> str:
    """Download a PDF from its mapped URL to a local directory if not already present.

    Args:
        pdf_name: Filename of the PDF (e.g. 'field-underwriting-manual-984e.pdf').
        dest_dir: Local directory to save the file. Defaults to 'data'.

    Returns:
        Local file path to the downloaded PDF.

    Raises:
        ValueError: If the PDF name has no mapped URL.
    """
    url = PDF_SOURCE_URLS.get(pdf_name)
    if url is None:
        raise ValueError(f"No URL mapped for '{pdf_name}'. Add it to PDF_SOURCE_URLS.")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, pdf_name)
    if os.path.exists(dest_path):
        logger.info(f"PDF already present at {dest_path}, skipping download.")
        return dest_path
    logger.info(f"Downloading {url} → {dest_path}")
    urllib.request.urlretrieve(url, dest_path)
    logger.info(f"Download complete: {dest_path}")
    return dest_path


def update_document_sources(documents: list, pdf_path: str) -> list:
    """Update document metadata to use source URLs instead of local paths.

    Args:
        documents: List of Document objects.
        pdf_path: Original PDF file path.

    Returns:
        List of documents with updated source metadata.
    """
    source_url = get_source_url(pdf_path)
    for doc in documents:
        if hasattr(doc, "metadata") and doc.metadata:
            doc.metadata["source"] = source_url
        doc.metadata["filename"] = pdf_path
    return documents


def get_documents(pdf_path: str = None, export_type: ExportType = None):
    """
    Loads documents from a PDF file using Docling.

    Args:
        pdf_path (str, optional): The path to the PDF file. Defaults to the field-underwriting-manual PDF.
        export_type (ExportType, optional): The export type for Docling. Defaults to global EXPORT_TYPE.
            - ExportType.DOC_CHUNKS: Returns pre-chunked documents from Docling
            - ExportType.MARKDOWN: Returns documents as markdown text

    Returns:
        list: A list of Document objects containing the loaded content.
    """
    if pdf_path is None:
        pdf_path = os.path.join("data", "iaa.pdf")

    if export_type is None:
        export_type = EXPORT_TYPE

    # For 'recursive' mode, load as markdown then split with RecursiveCharacterTextSplitter
    loader_export_type = (
        ExportType.MARKDOWN if export_type == "recursive" else export_type
    )
    loader = DoclingLoader(
        file_path=pdf_path, export_type=loader_export_type, converter=converter
    )
    documents = loader.load()

    # Update document sources to use URLs instead of local paths
    documents = update_document_sources(documents, pdf_path)

    source_url = get_source_url(pdf_path)
    logger.info(
        f"Loaded {len(documents)} documents from {pdf_path} (source: {source_url}) with export_type={export_type}"
    )
    return documents


# Split Data
def split_documents(
    documents,
    export_type: ExportType = None,
    chunk_token_size=500,
    chunk_token_overlap=50,
):
    """
    Splits a list of documents into smaller chunks based on the export type and configuration.

    Parameters:
    - documents (list): A list of documents to be split.
    - export_type (ExportType, optional): The export type used when loading. Defaults to global EXPORT_TYPE.
        - ExportType.DOC_CHUNKS: Documents are already chunked by Docling, returned as-is.
        - ExportType.MARKDOWN: Split by markdown headers (H1, H2, H3).
    - chunk_token_size (int): The maximum number of tokens in each chunk (used for fallback). Default is 500.
    - chunk_token_overlap (int): The number of tokens to overlap between adjacent chunks. Default is 50.

    Returns:
    - chunks (list): A list of chunks/splits from the documents.
    """
    if export_type is None:
        export_type = EXPORT_TYPE

    if export_type == ExportType.DOC_CHUNKS:
        # Documents are already chunked by Docling
        splits = documents
        logger.info(f"Using Docling DOC_CHUNKS: {len(splits)} chunks")
    elif export_type == ExportType.MARKDOWN:
        # Split markdown by headers
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header_1"),
                ("##", "Header_2"),
                ("###", "Header_3"),
            ],
        )
        splits = [
            split
            for doc in documents
            for split in splitter.split_text(doc.page_content)
        ]
        logger.info(f"Split markdown documents into {len(splits)} chunks by headers")
    elif export_type == "recursive":
        # Split using RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_token_size,
            chunk_overlap=chunk_token_overlap,
        )
        splits = splitter.split_documents(documents)
        logger.info(
            f"Split documents into {len(splits)} chunks using RecursiveCharacterTextSplitter"
        )
    else:
        raise ValueError(f"Unexpected export type: {export_type}")

    return splits


def chunk_documents(
    pdf_path: str = None,
    export_type: ExportType = None,
    chunk_token_size: int = 128,
    chunk_token_overlap: int = 16,
):
    """
    Complete pipeline to load and chunk documents from a PDF.

    Args:
        pdf_path (str, optional): Path to the PDF file. Defaults to the field-underwriting-manual PDF.
        export_type (ExportType, optional): Docling export type. Defaults to global EXPORT_TYPE.
        chunk_token_size (int): Token chunk size for fallback splitting. Default is 128.
        chunk_token_overlap (int): Token overlap for fallback splitting. Default is 16.

    Returns:
        list: List of document chunks.
    """
    if export_type is None:
        export_type = EXPORT_TYPE

    logger.info(f"Starting ingestion pipeline with export_type={export_type}")
    documents = get_documents(pdf_path, export_type=export_type)
    logger.info(f"Documents - {len(documents)} loaded.")
    chunks = split_documents(
        documents,
        export_type=export_type,
        chunk_token_size=chunk_token_size,
        chunk_token_overlap=chunk_token_overlap,
    )

    logger.info(f"Ending ingestion pipeline - {len(chunks)} chunks ingested.")
    return chunks


def run_ingestion(pdf_name: str, carrier: str) -> None:
    """Download and ingest a PDF into ChromaDB if the collection does not already exist.

    Args:
        pdf_name: Filename of the PDF to ingest (must be mapped in PDF_SOURCE_URLS).
        carrier: Carrier name used as the ChromaDB collection name (e.g. 'BESAFE').
    """
    carrier = carrier.strip()
    pdf_path = download_pdf(pdf_name, dest_dir=f"{PROJECT_ROOT}/data")
    vdb_dir = f"{PROJECT_ROOT}/{os.getenv('VDB_DIR', 'store')}"
    client = chromadb.PersistentClient(path=vdb_dir)

    existing_names = [c.name for c in client.list_collections()]
    if carrier in existing_names:
        count = client.get_collection(carrier).count()
        if count > 0:
            logger.info(
                f"Collection '{carrier}' already exists with {count} documents. Skipping ingestion."
            )
            return
        logger.info(f"Collection '{carrier}' exists but is empty. Re-ingesting.")
        client.delete_collection(carrier)

    logger.info(
        f"Starting ingestion: pdf={pdf_path}, carrier={carrier}, collection={carrier}"
    )
    sample_docs = chunk_documents(pdf_path=pdf_path, export_type=ExportType.DOC_CHUNKS)
    logger.info(f"Loaded {len(sample_docs)} chunks.")

    filtered_docs = filter_complex_metadata(sample_docs)
    Chroma.from_documents(
        filtered_docs,
        collection_name=carrier,
        collection_metadata={"description": "insurance life", "carrier": carrier},
        embedding=embeddings,
        persist_directory=vdb_dir,
    )
    logger.info(f"Ingestion complete. Collection '{carrier}' saved to {vdb_dir}.")
    logger.info(f"Collections: {client.list_collections()}")


def _ingest():
    run_ingestion("field-underwriting-manual-984e.pdf", "BESAFE")
    run_ingestion("iaa.pdf", "MOONLIFE")


# import threading
# threading.Thread(target=_ingest, daemon=True).start()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=".env")

    parser = argparse.ArgumentParser(description="Ingest a PDF into ChromaDB.")
    parser.add_argument(
        "--pdf",
        required=True,
        help="PDF filename to ingest (e.g. field-underwriting-manual-984e.pdf or iaa.pdf).",
    )
    parser.add_argument(
        "--carrier",
        required=True,
        help="Carrier name used as the ChromaDB collection name (e.g. BESAFE or MOONLIFE).",
    )
    args = parser.parse_args()

    run_ingestion(args.pdf, args.carrier)
