from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.schemas.tkp import ValidationReport


class TestAuthSchemas:
    def test_login_request_valid(self):
        r = LoginRequest(email="a@b.com", password="secret")
        assert r.email == "a@b.com"

    def test_login_request_missing_password_raises(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="a@b.com")

    def test_register_request_default_role(self):
        r = RegisterRequest(name="Alice", email="a@b.com", password="abc123")
        assert r.role == "teacher"

    def test_register_request_admin_role(self):
        r = RegisterRequest(name="Admin", email="admin@x.com", password="x", role="admin")
        assert r.role == "admin"

    def test_token_response(self):
        r = TokenResponse(access_token="a", refresh_token="b")
        assert r.token_type == "bearer"

    def test_refresh_request(self):
        r = RefreshRequest(refresh_token="tok")
        assert r.refresh_token == "tok"

    def test_user_response_from_attributes(self):
        data = {"id": "u1", "name": "Alice", "email": "a@b.com", "role": "teacher", "is_active": True}
        r = UserResponse.model_validate(data)
        assert r.id == "u1"
        assert r.role == "teacher"

    def test_user_response_email_required(self):
        with pytest.raises(ValidationError):
            UserResponse.model_validate({"id": "u1", "name": "N", "role": "teacher", "is_active": True})


class TestJobSchemas:
    def test_job_create_default_config(self):
        r = JobCreate(file_name="test.pdf")
        assert r.config == {}

    def test_job_create_with_config(self):
        r = JobCreate(file_name="x.pdf", config={"stage": 3})
        assert r.config["stage"] == 3

    def test_job_response_without_optional(self):
        r = JobResponse(id="j1", status="processing", current_stage=1, file_name="x.pdf", created_at=datetime.now(timezone.utc))
        assert r.error_message is None
        assert r.completed_at is None
        assert r.tkp_url is None

    def test_job_list_response(self):
        r = JobListResponse(jobs=[], total=0)
        assert r.total == 0


class TestValidationReport:
    def test_full_score(self):
        r = ValidationReport(
            schema_valid=True, completeness_score=1.0,
            missing_elements=[], consistency_issues=[], hallucination_flags=[],
        )
        assert r.completeness_score == 1.0

    def test_with_issues(self):
        r = ValidationReport(
            schema_valid=False, completeness_score=0.3,
            missing_elements=["knowledge_base"], consistency_issues=["gap"],
            hallucination_flags=["fact_x"],
        )
        assert len(r.hallucination_flags) == 1
