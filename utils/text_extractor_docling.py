# from docling.document_converter import DocumentConverter
# from typing import List, Union
# import os

# def extract_text(
#     source: Union[str, List[str]], export_format: str = "markdown"
# ) -> str:
#     """
#     Extracts text from a PDF file or list of image files using Docling.

#     Args:
#         source: A string (PDF file path) or a list of strings (image file paths).
#         export_format: "markdown", "json", "html", or "doctags"

#     Returns:
#         Extracted text in the selected format.
#     """
#     converter = DocumentConverter()

#     # Case 1: PDF file
#     if isinstance(source, str) and source.lower().endswith(".pdf"):
#         if not os.path.exists(source):
#             raise FileNotFoundError(f"PDF file not found: {source}")
#         result = converter.convert(source)

#     # Case 2: List of image file paths
#     elif isinstance(source, list) and all(os.path.isfile(p) for p in source):
#         # Convert each image file individually and combine results
#         results = []
#         for path in source:
#             result = converter.convert(path)
#             results.append(result)
        
#         # For now, return the first result's document
#         # In a more sophisticated implementation, you might want to merge multiple documents
#         result = results[0]

#     else:
#         raise ValueError("Source must be a PDF file path or a list of valid image file paths.")

#     # Export format handling
#     doc = result.document
#     if export_format == "markdown":
#         return doc.export_to_markdown()
#     elif export_format == "json":
#         return doc.export_to_json()
#     elif export_format == "html":
#         return doc.export_to_html()
#     elif export_format == "doctags":
#         return doc.export_to_doctags()
#     else:
#         raise ValueError(f"Unsupported export format: {export_format}")

