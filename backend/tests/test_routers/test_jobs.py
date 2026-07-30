import pytest
from app.models.job import Job
from app.models.user import User


class TestListJobs:
    async def test_list_jobs_empty(self, auth_client):
        resp = await auth_client.get("/api/jobs")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["jobs"] == []

    async def test_list_jobs_with_data(self, auth_client, db_session, test_user: User):
        db_session.add(Job(
            id="job-1", file_name="doc1.pdf", file_path="/tmp/doc1.pdf",
            user_id=test_user.id, status="completed",
        ))
        await db_session.flush()

        resp = await auth_client.get("/api/jobs")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["jobs"][0]["file_name"] == "doc1.pdf"
        assert body["jobs"][0]["status"] == "completed"

    async def test_list_jobs_only_own(self, auth_client, db_session, test_user: User):
        db_session.add(Job(
            id="job-own", file_name="own.pdf", file_path="/tmp/own.pdf",
            user_id=test_user.id,
        ))
        db_session.add(Job(
            id="job-other", file_name="other.pdf", file_path="/tmp/other.pdf",
            user_id="other-user-id",
        ))
        await db_session.flush()

        resp = await auth_client.get("/api/jobs")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestGetJob:
    async def test_get_job_found(self, auth_client, db_session, test_user: User):
        db_session.add(Job(
            id="job-detail", file_name="detail.pdf", file_path="/tmp/detail.pdf",
            user_id=test_user.id,
        ))
        await db_session.flush()

        resp = await auth_client.get("/api/jobs/job-detail")
        assert resp.status_code == 200
        assert resp.json()["id"] == "job-detail"

    async def test_get_job_not_found(self, auth_client):
        resp = await auth_client.get("/api/jobs/nonexistent-id")
        assert resp.status_code == 404

    async def test_get_other_users_job_returns_404(self, auth_client, db_session):
        db_session.add(Job(
            id="other-job", file_name="x.pdf", file_path="/tmp/x.pdf",
            user_id="not-my-user-id",
        ))
        await db_session.flush()

        resp = await auth_client.get("/api/jobs/other-job")
        assert resp.status_code == 404


class TestDeleteJob:
    async def test_delete_job(self, auth_client, db_session, test_user: User):
        db_session.add(Job(
            id="job-del", file_name="del.pdf", file_path="/tmp/del.pdf",
            user_id=test_user.id,
        ))
        await db_session.flush()

        resp = await auth_client.delete("/api/jobs/job-del")
        assert resp.status_code == 200

        get_resp = await auth_client.get("/api/jobs/job-del")
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_job(self, auth_client):
        resp = await auth_client.delete("/api/jobs/no-such-id")
        assert resp.status_code == 404


class TestHealth:
    async def test_health_endpoint(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
