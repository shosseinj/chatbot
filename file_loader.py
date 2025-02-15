from dataclasses import dataclass
from pathlib import Path

from pypdfium2 import PdfDocument
from streamlit.runtime.uploaded_file_manager import UploadedFile

from cogvault.config import Config
import openparse
TEXT_FILE_EXTENSION = ".txt"
MD_FILE_EXTENSION = ".md"
PDF_EXTENSION = ".pdf"

@dataclass
class File:
    name: str
    content: str

def extract_pdf_content(data: bytes) -> str:
    # pdf = PdfDocument(data)  # this is str : uploads/1.pdf
    # content = ""
    # for page in pdf:
    #     text_page = page.get_textpage()
    #     content += f"{text_page.get_text_bounded()}\n"
    # return content

    parser = openparse.DocumentParser()
    parsed_doc = parser.parse(data)

    # chunks = []
    # print('jaber')
    text_content = ""
    for nod in parsed_doc.nodes:
        text_content += "\n\n\n\n"
        for element in nod.elements:
            if hasattr(element, 'text'):

                text_content += element.text
        # text_content += "".join(element.text for element in nod.elements if hasattr(element, 'text'))
    #     if len(text_content.strip()) > 50:
    #         chunks.append(text_content.strip())
    #
    # doc_objects = [
    #     Document(page_content=chunk, metadata={"chunk_id": i, "asset_id": asset_id})
    #     for i, chunk in enumerate(chunks)
    # ]
    # print("Chunking complete...")
    # vector_store = FAISS.from_documents(doc_objects, embeddings)
    # vector_stores[asset_id] = vector_store
    # documents[asset_id] = {"file_path": file_path}
    # print('Processing finished.')
    # r.1:5000
# Press CTRL+C to quiteturn parsed_doc
    return text_content

def load_uploaded_file(uploaded_file: UploadedFile) -> File:
    file_extension = Path(uploaded_file).suffix

    if file_extension not in Config.ALLOWED_FILE_EXTENSIONS:
        raise ValueError(f"Invalid file extension: {file_extension} for file {uploaded_file.name}")

    if file_extension == PDF_EXTENSION:
        content = extract_pdf_content(uploaded_file)
        return File(name=uploaded_file, content=content)
    if file_extension == TEXT_FILE_EXTENSION:


        try:
            with open(uploaded_file, 'r', encoding='utf-8') as file:
                content = file.read()
                # print(content)
        except FileNotFoundError:
            print(f"The file '{uploaded_file}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return File(name=uploaded_file, content=content)

    value = uploaded_file.getvalue().decode("utf-8")
    return File(name=uploaded_file, content= value)




