import uuid

from sqlalchemy import Column, Integer, String, inspect
from sqlalchemy.orm import DeclarativeMeta

from app.models.user import User
from app.models.job import Job
from app.models.llm_cache import LLMCache


def _table_columns(model: DeclarativeMeta) -> dict:
    mapper = inspect(model)
    return {c.name: c for c in mapper.columns}


class TestUserModel:
    def test_user_creation(self):
        u = User(name="Alice", email="a@b.com", password_hash="hash123", role="teacher")
        assert u.name == "Alice"
        assert u.email == "a@b.com"

    def test_user_pk_is_uuid(self):
        raw = str(uuid.uuid4())
        u = User(id=raw, name="N", email="e@b.com", password_hash="h", role="teacher")
        assert u.id == raw
        assert len(u.id) == 36

    def test_user_table_structure(self):
        cols = _table_columns(User)
        assert cols["role"].default.arg == "teacher"
        assert cols["is_active"].default.arg is True

    def test_user_representation(self):
        u = User(name="Bob", email="bob@x.com", password_hash="h", role="admin")
        assert "bob@x.com" in repr(u)


class TestJobModel:
    def test_job_creation(self):
        j = Job(id="j1", file_name="doc.pdf", file_path="/tmp/doc.pdf", user_id="u1")
        assert j.file_name == "doc.pdf"

    def test_job_with_different_statuses(self):
        for s in ("pending", "processing", "completed", "failed"):
            j = Job(id=f"j_{s}", file_name="f.pdf", file_path="/tmp/f.pdf", user_id="u1", status=s)
            assert j.status == s

    def test_job_table_structure(self):
        cols = _table_columns(Job)
        assert cols["status"].default.arg == "pending"
        assert cols["current_stage"].default.arg == 0

    def test_job_representation(self):
        j = Job(id="j1", file_name="x.pdf", file_path="/tmp/x.pdf", user_id="u1")
        assert "j1" in repr(j)


class TestLLMCacheModel:
    def test_cache_creation(self):
        c = LLMCache(prompt_hash="abc123def456", response="output", model="gemini")
        assert c.prompt_hash == "abc123def456"
        assert c.response == "output"
        assert c.model == "gemini"

    def test_cache_table_structure(self):
        cols = _table_columns(LLMCache)
        assert cols["tokens_used"].default.arg == 0
