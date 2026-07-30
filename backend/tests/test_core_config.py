from app.core.config import Settings


class TestSettingsDefaults:
    def test_uses_env_vars_when_set(self):
        s = Settings()
        assert s.JWT_SECRET_KEY == "test-secret-key-for-testing"

    def test_fallback_defaults(self):
        s = Settings()
        assert s.APP_NAME == "Teacher AI Platform"
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert s.JWT_ALGORITHM == "HS256"
        assert s.MAX_UPLOAD_SIZE == 10485760

    def test_api_keys_property_splits_comma(self):
        s = Settings()
        assert "test-key-1" in s.api_keys

    def test_fallback_models_splits_comma(self):
        s = Settings()
        assert "gemini-2.0-flash" in s.fallback_models

    def test_cors_origins_parses_json(self):
        s = Settings()
        assert "http://localhost:5173" in s.CORS_ORIGINS
