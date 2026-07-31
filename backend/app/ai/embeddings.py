from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.core.logging_config import logger


class LocalEmbeddings(Embeddings):
    provider_name = "local"

    def __init__(self):
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings

            logger.info(
                "using_local_embedding_model", model=settings.LOCAL_EMBEDDING_MODEL
            )
            self._ef = HuggingFaceEmbeddings(model_name=settings.LOCAL_EMBEDDING_MODEL)
        except Exception as e:
            logger.warning("local_embedding_fallback_activated", error=str(e))
            self._ef = None

    def _hash_embed(self, text: str, dim: int = 768) -> list[float]:
        import hashlib

        vec = [0.0] * dim
        words = text.lower().split()
        for w in words:
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            val = ((h >> 8) % 200 - 100) / 100.0
            vec[idx] += val
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._ef:
            try:
                return self._ef.embed_documents(texts)
            except Exception:
                pass
        return [self._hash_embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        if self._ef:
            try:
                return self._ef.embed_query(text)
            except Exception:
                pass
        return self._hash_embed(text)


class GoogleEmbeddings(Embeddings):
    """Exactly one embedding backend is active at a time.

    Google is used when any configured key answers the probe; otherwise the
    local model is used. The inactive backend is never constructed, so only
    one model is ever loaded in memory.
    """

    def __init__(self):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        self._ef = None
        self._local = None
        for key in settings.api_keys:
            try:
                ef = GoogleGenerativeAIEmbeddings(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    google_api_key=key,
                    output_dimensionality=settings.EMBEDDING_DIMENSION,
                )
                probe = ef.embed_query("ping")
                if probe:
                    self._ef = ef
                    logger.info(
                        "using_google_embedding_model",
                        model=settings.GEMINI_EMBEDDING_MODEL,
                        key_preview=key[:6],
                        dim=len(probe),
                    )
                    return
            except Exception as e:
                logger.warning(
                    "google_embedding_key_failed",
                    key_preview=key[:6] if key else "none",
                    error=str(e)[:200],
                )
        self._local = LocalEmbeddings()
        logger.warning("google_embedding_unavailable_using_local")

    @property
    def provider_name(self) -> str:
        return "google" if self._ef else "local"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._ef:
            return self._ef.embed_documents(texts)
        if self._local is None:
            raise RuntimeError("no embedding backend available")
        return self._local.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        if self._ef:
            return self._ef.embed_query(text)
        if self._local is None:
            raise RuntimeError("no embedding backend available")
        return self._local.embed_query(text)


_embeddings_instance: Embeddings | None = None


def get_embeddings() -> Embeddings:
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = GoogleEmbeddings()
    return _embeddings_instance


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
        collection_name = "hybrid"
        self.vectorstore = Chroma.from_documents(
            docs,
            self.embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR,
            collection_name=collection_name,
        )
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
