from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio


class TestUploadDocument:
    UPLOAD_URL = "/api/upload"

    async def _register_and_login(self, client, email="upload-test@gyansetu.ai"):
        reg_resp = await client.post("/api/auth/register", json={
            "name": "Upload Test",
            "email": email,
            "password": "Test@123",
        })
        login_resp = await client.post("/api/auth/login", json={
            "email": email,
            "password": "Test@123",
        })
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_upload_pdf_success(self, client):
        headers = await self._register_and_login(client, "upload-pdf@gyansetu.ai")
        with patch("app.routers.upload.run_pipeline", new_callable=AsyncMock) as mock_run:
            resp = await client.post(
                self.UPLOAD_URL,
                headers=headers,
                files={"file": ("test.pdf", b"%PDF-1.4 sample", "application/pdf")},
                data={
                    "period_duration": 40,
                    "num_periods": 0,
                    "target_language": "English",
                    "board_alignment": "CBSE",
                },
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pending"
        assert "job_id" in body
        mock_run.assert_called_once()

    async def test_upload_docx_success(self, client):
        headers = await self._register_and_login(client, "upload-docx@gyansetu.ai")
        with patch("app.routers.upload.run_pipeline", new_callable=AsyncMock):
            resp = await client.post(
                self.UPLOAD_URL,
                headers=headers,
                files={"file": ("notes.docx", b"PK\x03\x04 sample docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"period_duration": 45, "target_language": "Hindi"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pending"

    async def test_upload_pptx_success(self, client):
        headers = await self._register_and_login(client, "upload-pptx@gyansetu.ai")
        with patch("app.routers.upload.run_pipeline", new_callable=AsyncMock):
            resp = await client.post(
                self.UPLOAD_URL,
                headers=headers,
                files={"file": ("slides.pptx", b"PK\x03\x04 sample pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
                data={"period_duration": 40},
            )
        assert resp.status_code == 200

    async def test_upload_txt_success(self, client):
        headers = await self._register_and_login(client, "upload-txt@gyansetu.ai")
        with patch("app.routers.upload.run_pipeline", new_callable=AsyncMock):
            resp = await client.post(
                self.UPLOAD_URL,
                headers=headers,
                files={"file": ("notes.txt", b"plain text content", "text/plain")},
                data={"period_duration": 40},
            )
        assert resp.status_code == 200

    async def test_upload_unsupported_file_type(self, client):
        headers = await self._register_and_login(client, "upload-unsup@gyansetu.ai")
        resp = await client.post(
            self.UPLOAD_URL,
            headers=headers,
            files={"file": ("image.png", b"PNG content", "image/png")},
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    async def test_upload_too_large(self, client):
        headers = await self._register_and_login(client, "upload-large@gyansetu.ai")
        from app.core.config import settings
        with patch.object(settings, "MAX_UPLOAD_SIZE", 100):
            resp = await client.post(
                self.UPLOAD_URL,
                headers=headers,
                files={"file": ("big.pdf", b"x" * 200, "application/pdf")},
                data={"period_duration": 40},
            )
        assert resp.status_code == 413

    async def test_upload_without_auth(self, client):
        resp = await client.post(
            self.UPLOAD_URL,
            files={"file": ("test.pdf", b"content", "application/pdf")},
        )
        assert resp.status_code in (401, 403)

    async def test_upload_missing_file_field(self, client):
        headers = await self._register_and_login(client, "upload-nofile@gyansetu.ai")
        resp = await client.post(
            self.UPLOAD_URL,
            headers=headers,
            data={"period_duration": 40},
        )
        assert resp.status_code == 422
