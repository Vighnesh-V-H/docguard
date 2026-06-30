from app.core.config import Settings


def test_settings_expose_logging_defaults() -> None:
    settings = Settings()

    assert settings.LOG_LEVEL == "INFO"
    assert settings.LOG_FORMAT == "text"
    assert settings.APP_NAME == "DocGuard AI"
    assert settings.API_V1_PREFIX == "/api/v1"
