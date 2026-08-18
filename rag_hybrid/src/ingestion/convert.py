from docling.document_converter import DocumentConverter
from pathlib import Path
import sys
from pprint import pprint
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import RESOURCES_DIR


def retrieve_documents():
    data_folder_path = RESOURCES_DIR
    docs = [item for item in data_folder_path.iterdir() if item.is_file()]
    return docs

# docs = retrieve_documents() 

def convert_documents(docs):
    converter = DocumentConverter()
    docling_docs = [converter.convert(doc_path).document for doc_path in docs]
    return docling_docs

if __name__ == "__main__":
    docs = retrieve_documents()
    docs = convert_documents(docs) 
    # print(f"Converted {len(docs)} documents from {len(docs)} files")
    pprint(f'First doc object content: {docs[0].texts}')


