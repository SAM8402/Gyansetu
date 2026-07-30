from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from rank_bm25 import BM25Okapi
from app.core.config import settings
from app.core.logging_config import logger


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Initialise and return the Google Generative AI embedding model.

    Returns:
        A GoogleGenerativeAIEmbeddings instance.
    """
    api_keys = settings.api_keys
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_keys[0] if api_keys else None,
    )


def chunk_document(text: str, metadata: dict = None) -> list[Document]:
    """Split a document into overlapping chunks for downstream processing.

    Args:
        text: Raw document text.
        metadata: Optional dictionary of metadata attached to every chunk.

    Returns:
        List of Document chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    docs = splitter.create_documents([text], [metadata or {}])
    return docs


class HybridRetriever:
    """Retriever that fuses dense vector search with sparse BM25 scoring."""

    def __init__(self, docs: list[Document]):
        """Initialise the retriever with a corpus of documents.

        Args:
            docs: Source document list.
        """
        self.embeddings = get_embeddings()
        self.vectorstore = Chroma.from_documents(docs, self.embeddings)
        self.bm25 = BM25Okapi([d.page_content.split() for d in docs])
        self.docs = docs

    def hybrid_search(self, query: str, k: int = 5) -> list[Document]:
        """Run a hybrid search combining vector similarity and BM25 scores.

        Args:
            query: Natural-language search query.
            k: Number of top results to return.

        Returns:
            Deduplicated list of Documents.
        """
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
        """Async wrapper around :meth:`hybrid_search`.

        Args:
            query: Natural-language search query.
            k: Number of top results to return.

        Returns:
            Deduplicated list of Documents.
        """
        return self.hybrid_search(query, k)
