import pytest


class TestRegister:
    async def test_register_success(self, client):
        resp = await client.post("/api/auth/register", json={
            "name": "New User",
            "email": "new@gyansetu.ai",
            "password": "secret123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client, test_user):
        resp = await client.post("/api/auth/register", json={
            "name": "Duplicate",
            "email": "test@gyansetu.ai",
            "password": "secret123",
        })
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()

    async def test_register_missing_fields(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "only@email.com",
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client, test_user):
        resp = await client.post("/api/auth/login", json={
            "email": "test@gyansetu.ai",
            "password": "testpass",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body

    async def test_login_wrong_password(self, client, test_user):
        resp = await client.post("/api/auth/login", json={
            "email": "test@gyansetu.ai",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/auth/login", json={
            "email": "nobody@gyansetu.ai",
            "password": "x",
        })
        assert resp.status_code == 401


class TestRefresh:
    async def test_refresh_success(self, client, test_user):
        login = await client.post("/api/auth/login", json={
            "email": "test@gyansetu.ai",
            "password": "testpass",
        })
        refresh_token = login.json()["refresh_token"]

        resp = await client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_refresh_invalid_token(self, client):
        resp = await client.post("/api/auth/refresh", json={
            "refresh_token": "garbage-token",
        })
        assert resp.status_code == 401

    async def test_refresh_access_token_rejected(self, client, test_user):
        login = await client.post("/api/auth/login", json={
            "email": "test@gyansetu.ai",
            "password": "testpass",
        })
        access_token = login.json()["access_token"]

        resp = await client.post("/api/auth/refresh", json={
            "refresh_token": access_token,
        })
        assert resp.status_code == 401
