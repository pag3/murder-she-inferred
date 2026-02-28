"""Tests for project-local settings resolution."""

from __future__ import annotations

import pytest

import murder_she_inferred.settings as settings


def test_prefers_environment_variable(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    monkeypatch.setenv(settings.DATA_DIR_ENV_VAR, str(data_dir))
    monkeypatch.setattr(settings, "_DOTENV_LOADED", True)

    assert settings.get_data_dir() == data_dir.resolve()


def test_default_data_dir_when_env_missing(monkeypatch, tmp_path):
    default_dir = tmp_path / "murder-she-inferred-data"
    default_dir.mkdir()

    monkeypatch.delenv(settings.DATA_DIR_ENV_VAR, raising=False)
    monkeypatch.setattr(settings, "DEFAULT_DATA_DIR", default_dir)
    monkeypatch.setattr(settings, "_DOTENV_LOADED", True)

    assert settings.get_data_dir() == default_dir.resolve()


def test_raises_for_missing_data_dir(monkeypatch, tmp_path):
    missing_dir = tmp_path / "missing-data"
    monkeypatch.delenv(settings.DATA_DIR_ENV_VAR, raising=False)
    monkeypatch.setattr(settings, "DEFAULT_DATA_DIR", missing_dir)
    monkeypatch.setattr(settings, "_DOTENV_LOADED", True)

    with pytest.raises(FileNotFoundError, match="Data directory does not exist"):
        settings.get_data_dir()


def test_data_path_joins_segments(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    transcripts = data_dir / "transcripts"
    transcripts.mkdir(parents=True)
    target = transcripts / "ep1.txt"
    target.write_text("hello", encoding="utf-8")

    monkeypatch.setenv(settings.DATA_DIR_ENV_VAR, str(data_dir))
    monkeypatch.setattr(settings, "_DOTENV_LOADED", True)

    assert settings.data_path("transcripts", "ep1.txt") == target


def test_loads_project_dotenv(monkeypatch, tmp_path):
    project_root = tmp_path / "repo"
    project_root.mkdir()
    dotenv_file = project_root / ".env"
    dotenv_file.write_text(
        f"{settings.DATA_DIR_ENV_VAR}=../private-data\n",
        encoding="utf-8",
    )

    monkeypatch.delenv(settings.DATA_DIR_ENV_VAR, raising=False)
    monkeypatch.setattr(settings, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(settings, "DEFAULT_DATA_DIR", project_root / "../ignored")
    monkeypatch.setattr(settings, "_DOTENV_LOADED", False)

    resolved = settings.get_data_dir(must_exist=False)
    assert resolved == (project_root / "../private-data").resolve(strict=False)
