from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.core.logging_config import logger


class LocalEmbeddings(Embeddings):
    def __init__(self):
        from langchain_community.embeddings import HuggingFaceEmbeddings
        logger.info("using_local_embedding_model", model="all-MiniLM-L6-v2")
        self._ef = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._ef.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._ef.embed_query(text)


def get_embeddings() -> Embeddings:
    return LocalEmbeddings()


def chunk_document(text: str, metadata: dict | None = None) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    docs = splitter.create_documents([text], [metadata or {}])
    return docs


class HybridRetriever:
    def __init__(self, docs: list[Document]):
        self.embeddings = get_embeddings()
        self.vectorstore = Chroma.from_documents(docs, self.embeddings, persist_directory=settings.CHROMA_PERSIST_DIR)
        self.bm25 = BM25Okapi([d.page_content.split() for d in docs])
        self.docs = docs

    def hybrid_search(self, query: str, k: int = 5) -> list[Document]:
        vector_results = self.vectorstore.similarity_search(query, k=k)

        bm25_scores = self.bm25.get_scores(query.split())
        bm25_indices = sorted(
            range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
        )[:k]
        bm25_results = [self.docs[i] for i in bm25_indices]

        seen = set()
        merged = []
        for doc in vector_results + bm25_results:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                merged.append(doc)
        return merged[:k]

    async def ahybrid_search(self, query: str, k: int = 5) -> list[Document]:
        return self.hybrid_search(query, k)
