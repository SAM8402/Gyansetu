"""Tests for the embedding backend selection (Google-first, local fallback)."""

from unittest.mock import MagicMock, patch

import pytest

from app.ai.embeddings import GoogleEmbeddings, LocalEmbeddings, get_embeddings
from app.core.config import settings

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def reset_embeddings_cache():
    """Ensure the memoized get_embeddings() instance does not leak between tests."""
    import app.ai.embeddings as emb

    saved = emb._embeddings_instance
    emb._embeddings_instance = None
    yield
    emb._embeddings_instance = saved


@pytest.fixture
def no_google_keys(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "")
    yield


# ── GoogleEmbeddings ──────────────────────────────────────────────────────────


class TestGoogleEmbeddings:
    def test_uses_first_working_key(self, no_google_keys, monkeypatch):
        """Google backend is chosen, probing each configured key in order."""
        calls = []

        def fake_ctor(*args, **kwargs):
            key = kwargs.get("google_api_key")
            calls.append(key)
            if key != "valid_key_3":
                raise RuntimeError("invalid api key")
            ef = MagicMock()
            ef.embed_query.return_value = [0.1, 0.2, 0.3]
            return ef

        monkeypatch.setattr(
            settings,
            "GOOGLE_API_KEY",
            "invalid_key_1,invalid_key_2,valid_key_3",
        )
        with (
            patch("app.ai.embeddings.LocalEmbeddings") as mock_local,
            patch(
                "langchain_google_genai.GoogleGenerativeAIEmbeddings",
                side_effect=fake_ctor,
            ) as mock_ctor,
        ):
            instance = GoogleEmbeddings()

        assert calls == ["invalid_key_1", "invalid_key_2", "valid_key_3"]
        assert mock_ctor.call_count == 3
        mock_local.assert_not_called()
        assert instance.provider_name == "google"
        assert instance._ef is not None
        assert instance._local is None

    def test_falls_back_to_local_when_all_keys_fail(self, no_google_keys, monkeypatch):
        """All keys failing yields a local-backed instance."""
        monkeypatch.setattr(settings, "GOOGLE_API_KEY", "bad_1,bad_2")

        def failing_ctor(*args, **kwargs):
            raise RuntimeError("invalid api key")

        with (
            patch("app.ai.embeddings.LocalEmbeddings") as mock_local,
            patch(
                "langchain_google_genai.GoogleGenerativeAIEmbeddings",
                side_effect=failing_ctor,
            ),
        ):
            instance = GoogleEmbeddings()

        mock_local.assert_called_once()
        assert instance.provider_name == "local"
        assert instance._ef is None
        assert instance._local is not None

    def test_skips_all_when_no_keys_configured(self, no_google_keys):
        """With no keys configured, Google is never instantiated and local is used."""
        with (
            patch("app.ai.embeddings.LocalEmbeddings") as mock_local,
            patch("langchain_google_genai.GoogleGenerativeAIEmbeddings") as mock_ctor,
        ):
            instance = GoogleEmbeddings()

        mock_ctor.assert_not_called()
        mock_local.assert_called_once()
        assert instance.provider_name == "local"

    def test_google_query_error_propagates(self, no_google_keys, monkeypatch):
        """When Google is active, a call failure surfaces; local is never loaded."""
        monkeypatch.setattr(settings, "GOOGLE_API_KEY", "valid_key")
        with (
            patch("app.ai.embeddings.LocalEmbeddings") as mock_local,
            patch("langchain_google_genai.GoogleGenerativeAIEmbeddings") as mock_ctor,
        ):
            google_ef = MagicMock()
            google_ef.embed_query.side_effect = [
                [0.1, 0.2, 0.3],
                RuntimeError("quota exceeded"),
            ]
            mock_ctor.return_value = google_ef

            instance = GoogleEmbeddings()

            with pytest.raises(RuntimeError, match="quota exceeded"):
                instance.embed_query("hello")

        mock_local.assert_not_called()

    def test_google_documents_error_propagates(self, no_google_keys, monkeypatch):
        """A Google documents failure propagates; local is never loaded."""
        monkeypatch.setattr(settings, "GOOGLE_API_KEY", "valid_key")
        with (
            patch("app.ai.embeddings.LocalEmbeddings") as mock_local,
            patch("langchain_google_genai.GoogleGenerativeAIEmbeddings") as mock_ctor,
        ):
            google_ef = MagicMock()
            google_ef.embed_query.return_value = [0.1, 0.2, 0.3]
            google_ef.embed_documents.side_effect = RuntimeError("quota exceeded")
            mock_ctor.return_value = google_ef

            instance = GoogleEmbeddings()

            with pytest.raises(RuntimeError, match="quota exceeded"):
                instance.embed_documents(["a", "b"])

        mock_local.assert_not_called()


# ── get_embeddings ────────────────────────────────────────────────────────────


class TestGetEmbeddings:
    def test_memoized(self, no_google_keys, reset_embeddings_cache):
        """Repeated calls return the same cached instance."""
        with patch("app.ai.embeddings.LocalEmbeddings"):
            first = get_embeddings()
            second = get_embeddings()

        assert first is second
        assert isinstance(first, GoogleEmbeddings)

    def test_returns_google_embeddings_when_key_works(
        self, no_google_keys, reset_embeddings_cache, monkeypatch
    ):
        monkeypatch.setattr(settings, "GOOGLE_API_KEY", "valid_key")
        with (
            patch("app.ai.embeddings.LocalEmbeddings"),
            patch("langchain_google_genai.GoogleGenerativeAIEmbeddings") as mock_ctor,
        ):
            mock_ctor.return_value.embed_query.return_value = [0.1, 0.2, 0.3]
            instance = get_embeddings()

        assert instance.provider_name == "google"
        assert instance.embed_query("ping") == [0.1, 0.2, 0.3]

    def test_falls_back_to_local_when_no_keys(
        self, no_google_keys, reset_embeddings_cache
    ):
        """Without any key, get_embeddings returns a local-backed instance."""
        with patch("app.ai.embeddings.LocalEmbeddings") as mock_local:
            instance = get_embeddings()

        mock_local.assert_called_once()
        assert instance.provider_name == "local"

    def test_local_embeddings_still_usable(self, no_google_keys):
        """LocalEmbeddings keeps working directly and reports its provider name."""
        instance = LocalEmbeddings()
        instance._ef = None

        assert instance.provider_name == "local"
        assert len(instance.embed_query("linear algebra")) == 768
