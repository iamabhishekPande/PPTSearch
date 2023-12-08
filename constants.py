import os
# from chromadb.config import Settings
from langchain.document_loaders import CSVLoader, PDFMinerLoader, TextLoader, UnstructuredExcelLoader, Docx2txtLoader, UnstructuredPowerPointLoader

ROOT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
SOURCE_DIRECTORY = os.path.join(ROOT_DIRECTORY, "source_documents")
PERSIST_DIRECTORY = os.path.join(ROOT_DIRECTORY, "DB")

# Can be changed to a specific number
INGEST_THREADS = os.cpu_count() or 8

# # Define the updated Chroma settings
# CHROMA_SETTINGS = {
#     "database": {
#         "implementation": "duckdb+parquet",
#         "persist_directory": PERSIST_DIRECTORY,
#         "anonymized_telemetry": False
#     }
# }

DOCUMENT_MAP = {
    # ".txt": TextLoader,
    # ".md": TextLoader,
    # ".py": TextLoader,
    # ".pdf": PDFMinerLoader,
    # ".csv": CSVLoader,
    # ".xls": UnstructuredExcelLoader,
    # ".xlsx": UnstructuredExcelLoader,
    # ".docx": Docx2txtLoader,
    # ".doc": Docx2txtLoader,
    ".ppt": UnstructuredPowerPointLoader,
    ".pptx": UnstructuredPowerPointLoader
}
