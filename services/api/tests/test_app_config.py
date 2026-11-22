from services.api.config import Settings


def test_settings_reject_invalid_api_prefix(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/ngit")
    monkeypatch.setenv("API_PREFIX", "relative")
    settings = Settings.from_env()
    try:
        assert False, "invalid prefix should be rejected"
    except ValueError:
        pass
