from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from cogvault.config import Config
from cogvault.file_loader import File

CONTEXT_PROMPT = ChatPromptTemplate.from_template(
    """
    You're an expert in document analysis. Your task is to provide brief, relevant context for a chunk of the given document.

    Here is the document:
    <document>
    {document}
    </document>

    Here is the chunk we want to situate within the whole document:
    <chunk>
    {chunk}
    </chunk>


Provide a concise context (2-3 sentences) for this chunk, considering the following guidelines:
1. Identify the main topic or concept discussed in the chunk.
2. Mention any relevant information or comparisons from the broader document context.
3. If applicable, note how this information relates to the overall theme or purpose of the document.
4. Include any key figures, dates, or percentages that provide important context.
5. Do not use phrases like "This chunk discusses" or "This section provides". Instead, directly state the context.

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.

Context:
""".strip()
)


# CONTEXT_PROMPT = ChatPromptTemplate.from_template(
#     """
#     تو به عنوان یک متخصص در تحلیل و آنالیز متن قراره فعالیت بکنی. کار تو ارايه محتوای مربوط، خلاصه برای یک بخشی (chunk) از متن داده شده، هستش.
#
#     متن به این صورت هستش:
#
#     <document>
#     {document}
#     </document>
#
#     در زیر بخشی (chunk) از داده هستش که ما میخواهیم در کل متن داده شده، موقعیت یابی بشه؛
#
#     <chunk>
#     {chunk}
#     </chunk>
#
# یک محتوای مختصر (2-3 جمله) برای این بخش (chunk) با در نظر گرفتن دستورالعمل های زیر ارائه دهید:
# 1. موضوع یا مفهوم اصلی مورد بحث در بخش را مشخص کنید.
# 2. هر گونه اطلاعات مرتبط یا مقایسه را از زمینه سند گسترده تر ذکر کنید.
# 3. در صورت امکان، در نظر بگیر که این اطلاعات بخش مذکور چگونه با موضوع یا هدف کلی متن اصلی مرتبط است.
# 4. ارقام، نتیجه، تاریخ یا درصدهای مهم را که اطلاعات مهمی را ارائه می دهند رو هم در نظر بگیر.
# 5. از عباراتی مانند "این بخش بیان می کند" یا "این بخش ارائه می دهد" استفاده نکن. در عوض، به طور مستقیم محتوا را بیان کن.
#
# لطفاً یک محتوای مختصر و مفید برای موقعیت یابی این بخش در متن اصلی به منظور بهبود بازیابی این بخش ارائه بده.
#
#
# محتوا:
# """.strip()
# )

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=Config.Preprocessing.CHUNK_SIZE,
    chunk_overlap=Config.Preprocessing.CHUNK_OVERLAP,
)

def create_llm() -> ChatOllama:
    return ChatOllama(model=Config.Preprocessing.LLM, temperature=0, keep_alive=-1)


def create_embeddings() -> FastEmbedEmbeddings:
    return FastEmbedEmbeddings(model_name=Config.Preprocessing.EMBEDDING_MODEL)

def create_reranker() -> FlashrankRerank:
    return FlashrankRerank(
        model=Config.Preprocessing.RERANKER, top_n=Config.Chatbot.N_CONTEXT_RESULTS
    )

def _generate_context(llm: ChatOllama, document: str, chunk: str) -> str:
    messages = CONTEXT_PROMPT.format_messages(document=document, chunk=chunk)
    response = llm.invoke(messages)
    return response.content

def _create_chunks(document: Document) -> List[Document]:
    # chunks = text_splitter.split_documents([document])
    chunks =   document.page_content.split('\n\n')  # document.page_content.split('\n\n\n\n')

    # Remove any empty strings from the list
    chunks = [chunk for chunk in chunks if chunk.strip()]

    # Create a list of Document objects with the same metadata
    chunks = [Document(metadata=document.metadata, page_content=chunk) for chunk in chunks]

    if not Config.Preprocessing.CONTEXTUALIZE_CHUNKS:
        return chunks
    llm = create_llm()
    contextual_chunks = []
    print('Num of Chunk:', len(chunks))
    # for i, chunk in enumerate(chunks):
    #     print(f'{i} / {len(chunks)}')
    #     context = _generate_context(llm, document.page_content, chunk.page_content)
    #     chunk_with_context = f"{context}\n\n{chunk.page_content}"
    #     contextual_chunks.append(Document(page_content=chunk_with_context, metadata=chunk.metadata))
    # print('context')
    # return contextual_chunks
    return chunks

def ingest_files(files: List[File]) -> BaseRetriever:
    documents = [Document(file.content, metadata={"source": file.name}) for file in files]
    chunks = []
    for document in documents:
        chunks.extend(_create_chunks(document))

    semantic_retriever = InMemoryVectorStore.from_documents(
        chunks, create_embeddings()
    ).as_retriever(search_kwargs={"k": Config.Preprocessing.N_SEMANTIC_RESULTS})

    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = Config.Preprocessing.N_BM25_RESULTS

    ensemble_retriever = EnsembleRetriever(
        retrievers=[semantic_retriever, bm25_retriever],
        weights=[0.8, 0.2],
    )

    return ContextualCompressionRetriever(
        base_compressor = create_reranker(), base_retriever = ensemble_retriever
    )


