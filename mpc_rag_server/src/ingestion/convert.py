from docling.document_converter import DocumentConverter
from pathlib import Path

#retrieve documents
data_path = Path(__file__).parent.parent.parent / "data"
docs = [item for item in data_path.iterdir() if item.is_file()]

converter = DocumentConverter()
docling_docs = [converter.convert(doc_path).document for doc_path in docs]
# json_output = [docling_doc.export_to_dict() for docling_doc in docling_docs]

# print(json_output)
# for doc in docling_docs:
#     print(doc.export_to_dict())


