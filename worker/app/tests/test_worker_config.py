"""Worker smoke tests."""

from __future__ import annotations

from app.config import WorkerSettings, get_worker_settings


def test_settings_defaults() -> None:
    settings = WorkerSettings()
    assert settings.app_env == "development"
    assert settings.worker_sync_interval_seconds == 300
    assert settings.provider_name == "mock"


def test_settings_is_development() -> None:
    settings = WorkerSettings()
    assert settings.is_development is True


def test_settings_production_is_not_dev() -> None:
    settings = WorkerSettings(app_env="production")  # type: ignore[call-arg]
    assert settings.is_development is False


def test_get_worker_settings_cached() -> None:
    s1 = get_worker_settings()
    s2 = get_worker_settings()
    assert s1 is s2
