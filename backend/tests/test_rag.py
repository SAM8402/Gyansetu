"""Tests for the RAG pipeline components (embeddings, hybrid retriever, knowledge extractor)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.ai.embeddings import chunk_document, HybridRetriever
from app.services.knowledge_extractor import KnowledgeExtractorService


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_text() -> str:
    return (
        "Linear algebra is the branch of mathematics concerning linear equations and linear transformations. "
        * 20
    )


@pytest.fixture
def sample_metadata() -> dict:
    return {"source": "pdf", "file_name": "algebra_intro.pdf"}


@pytest.fixture
def mock_docs() -> list[Document]:
    return [
        Document(page_content="Vectors are quantities with magnitude and direction.", metadata={"source": "pdf"}),
        Document(page_content="Matrices are rectangular arrays of numbers.", metadata={"source": "pdf"}),
        Document(page_content="Eigenvalues describe the scaling factor of eigenvectors.", metadata={"source": "pdf"}),
    ]


@pytest.fixture
def mock_embeddings():
    with patch("app.ai.embeddings.get_embeddings") as m:
        emb = MagicMock()
        emb.embed_query.return_value = [0.1, 0.2, 0.3]
        emb.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        m.return_value = emb
        yield m


@pytest.fixture
def mock_chroma():
    with patch("langchain_chroma.Chroma.from_documents") as m:
        vs = MagicMock()
        vs.similarity_search.return_value = [
            Document(page_content="Matrices are rectangular arrays of numbers."),
            Document(page_content="Eigenvalues describe the scaling factor of eigenvectors."),
        ]
        m.return_value = vs
        yield m


@pytest.fixture
def mock_bm25():
    with patch("app.ai.embeddings.BM25Okapi") as m:
        bm25 = MagicMock()
        bm25.get_scores.return_value = [0.5, 0.8, 0.3]
        m.return_value = bm25
        yield m


# ── chunk_document ────────────────────────────────────────────────────────────


class TestChunkDocument:
    def test_returns_list_of_documents(self, sample_text):
        docs = chunk_document(sample_text)
        assert isinstance(docs, list)
        assert all(isinstance(d, Document) for d in docs)

    def test_each_chunk_has_content(self, sample_text):
        docs = chunk_document(sample_text)
        for d in docs:
            assert len(d.page_content) > 0

    def test_attaches_metadata(self, sample_text, sample_metadata):
        docs = chunk_document(sample_text, sample_metadata)
        for d in docs:
            assert d.metadata["source"] == "pdf"
            assert d.metadata["file_name"] == "algebra_intro.pdf"

    def test_uses_settings_chunk_size(self, sample_text):
        from app.core.config import settings

        docs = chunk_document(sample_text)
        for d in docs:
            assert len(d.page_content) <= settings.CHUNK_SIZE

    def test_empty_text_returns_empty_list(self):
        docs = chunk_document("")
        assert len(docs) == 0

    def test_smaller_text_than_chunk_size(self):
        text = "Short text."
        docs = chunk_document(text)
        assert len(text) < 500
        assert len(docs) >= 1

    def test_metadata_defaults_to_empty_dict(self, sample_text):
        docs = chunk_document(sample_text)
        for d in docs:
            assert d.metadata is not None


# ── HybridRetriever ──────────────────────────────────────────────────────────


class TestHybridRetrieverInit:
    def test_initialises_vectorstore_and_bm25(self, mock_embeddings, mock_chroma, mock_bm25, mock_docs):
        retriever = HybridRetriever(mock_docs)
        assert retriever.vectorstore is not None
        assert retriever.bm25 is not None
        assert retriever.docs == mock_docs


class TestHybridRetrieverSearch:
    def test_hybrid_search_returns_documents(self, mock_embeddings, mock_chroma, mock_bm25, mock_docs):
        retriever = HybridRetriever(mock_docs)
        results = retriever.hybrid_search("linear algebra", k=3)
        assert isinstance(results, list)
        assert all(isinstance(d, Document) for d in results)
        assert len(results) <= 3

    def test_hybrid_search_deduplicates(self, mock_embeddings, mock_chroma, mock_bm25, mock_docs):
        retriever = HybridRetriever(mock_docs)
        results = retriever.hybrid_search("matrices", k=5)
        contents = [d.page_content for d in results]
        assert len(contents) == len(set(contents))

    def test_hybrid_search_with_one_result(self, mock_embeddings, mock_chroma, mock_bm25, mock_docs):
        retriever = HybridRetriever(mock_docs)
        results = retriever.hybrid_search("linear algebra", k=1)
        assert len(results) <= 1

    def test_hybrid_search_calls_vectorstore(self, mock_embeddings, mock_chroma, mock_bm25, mock_docs):
        retriever = HybridRetriever(mock_docs)
        retriever.hybrid_search("test query", k=3)
        retriever.vectorstore.similarity_search.assert_called_once_with("test query", k=3)

    @pytest.mark.asyncio
    async def test_ahybrid_search_equals_hybrid(self, mock_embeddings, mock_chroma, mock_bm25, mock_docs):
        retriever = HybridRetriever(mock_docs)
        result = await retriever.ahybrid_search("linear algebra", k=2)
        expected = retriever.hybrid_search("linear algebra", k=2)
        assert [d.page_content for d in result] == [d.page_content for d in expected]


class TestHybridRetrieverWithRealData:
    def test_retriever_with_real_chunks(self):
        text = "Calculus is the mathematical study of continuous change. " * 15
        docs = chunk_document(text, {"source": "txt"})
        assert len(docs) >= 1

        with (
            patch("langchain_chroma.Chroma.from_documents") as mock_chroma,
            patch("app.ai.embeddings.BM25Okapi") as mock_bm25,
        ):
            vs = MagicMock()
            vs.similarity_search.return_value = [docs[0]]
            mock_chroma.return_value = vs
            mock_bm25_instance = MagicMock()
            mock_bm25_instance.get_scores.return_value = [1.0] * len(docs)
            mock_bm25.return_value = mock_bm25_instance

            retriever = HybridRetriever(docs)
            results = retriever.hybrid_search("calculus", k=3)
            assert len(results) >= 1


# ── KnowledgeExtractorService ─────────────────────────────────────────────────


class TestKnowledgeExtractorService:
    @pytest.fixture
    def service(self):
        return KnowledgeExtractorService()

    @pytest.fixture
    def doc_data(self) -> dict:
        return {
            "raw_text": "Linear algebra studies vector spaces and linear mappings between them. " * 20,
            "metadata": {"file_type": "pdf", "file_name": "linalg.pdf"},
        }

    @pytest.fixture
    def metadata(self) -> dict:
        return {"subject": "Mathematics", "topic": "Linear Algebra"}

    @pytest.mark.asyncio
    async def test_process_returns_dict(self, service, doc_data, metadata):
        with (
            patch("app.services.knowledge_extractor.chunk_document") as mock_chunk,
            patch("app.services.knowledge_extractor.HybridRetriever") as mock_hybrid,
            patch("app.services.knowledge_extractor.generate_json", new=AsyncMock(return_value={"concepts": []})),
        ):
            mock_chunk.return_value = [Document(page_content="dummy", metadata={})]
            mock_hybrid.return_value.hybrid_search.return_value = [Document(page_content="dummy", metadata={})]
            result = await service.process(doc_data, metadata)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_process_extracts_concepts(self, service, doc_data, metadata):
        expected = {
            "concepts": [{"name": "Vector Space", "definition": "A set of vectors closed under addition and scalar multiplication."}],
        }
        with (
            patch("app.services.knowledge_extractor.chunk_document") as mock_chunk,
            patch("app.services.knowledge_extractor.HybridRetriever") as mock_hybrid,
            patch("app.services.knowledge_extractor.generate_json", new=AsyncMock(return_value=expected)),
        ):
            mock_chunk.return_value = [Document(page_content="test", metadata={})]
            mock_hybrid.return_value.hybrid_search.return_value = [Document(page_content="test", metadata={})]
            result = await service.process(doc_data, metadata)
            assert result == expected

    @pytest.mark.asyncio
    async def test_process_calls_generate_json_with_subject_and_topic(self, service, doc_data, metadata):
        mock_generate = AsyncMock(return_value={"concepts": []})
        with (
            patch("app.services.knowledge_extractor.chunk_document") as mock_chunk,
            patch("app.services.knowledge_extractor.HybridRetriever") as mock_hybrid,
            patch("app.services.knowledge_extractor.generate_json", new=mock_generate),
        ):
            mock_chunk.return_value = [Document(page_content="Linear algebra content", metadata={})]
            mock_hybrid.return_value.hybrid_search.return_value = [Document(page_content="Linear algebra content", metadata={})]
            await service.process(doc_data, metadata)
            call_prompt = mock_generate.call_args[0][0]
            assert "Mathematics" in call_prompt
            assert "Linear Algebra" in call_prompt

    @pytest.mark.asyncio
    async def test_process_without_topic_still_works(self, service, doc_data):
        minimal_metadata = {"subject": "Physics"}
        with (
            patch("app.services.knowledge_extractor.chunk_document") as mock_chunk,
            patch("app.services.knowledge_extractor.HybridRetriever") as mock_hybrid,
            patch("app.services.knowledge_extractor.generate_json", new=AsyncMock(return_value={"concepts": []})),
        ):
            mock_chunk.return_value = [Document(page_content="dummy", metadata={})]
            mock_hybrid.return_value.hybrid_search.return_value = [Document(page_content="dummy", metadata={})]
            result = await service.process(doc_data, minimal_metadata)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_process_empty_text_returns_dict(self, service, metadata):
        doc_data = {"raw_text": "", "metadata": {"file_type": "txt"}}
        with (
            patch("app.services.knowledge_extractor.chunk_document") as mock_chunk,
            patch("app.services.knowledge_extractor.HybridRetriever") as mock_hybrid,
            patch("app.services.knowledge_extractor.generate_json", new=AsyncMock(return_value={})),
        ):
            mock_chunk.return_value = []
            mock_hybrid.return_value.hybrid_search.return_value = []
            result = await service.process(doc_data, metadata)
            assert isinstance(result, dict)
