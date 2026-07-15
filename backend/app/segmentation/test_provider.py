import os
import sys

from app.segmentation.fixture_provider import FixtureProvider
from app.segmentation.provider_factory import get_segmentation_provider


def test_fixture_provider_uses_matching_fixture_for_uploaded_filename(tmp_path):
    provider = FixtureProvider(fixtures_dir=tmp_path)

    fixture_dir = tmp_path
    (fixture_dir / "default.json").write_text('{"coralId": "default", "image": {"width": 100, "height": 100}, "segments": []}', encoding="utf-8")
    (fixture_dir / "islalarga_c005.json").write_text('{"coralId": "c005", "image": {"width": 100, "height": 100}, "segments": []}', encoding="utf-8")

    result = provider.segment(image=None, image_filename="CR_IslaLarga_T01_c005.JPG")

    assert result.image_width == 100
    assert result.image_height == 100
    assert result.segments == []


def test_fixture_provider_falls_back_to_default_for_unknown_fixture(tmp_path):
    provider = FixtureProvider(fixtures_dir=tmp_path)

    (tmp_path / "default.json").write_text('{"coralId": "default", "image": {"width": 100, "height": 100}, "segments": []}', encoding="utf-8")

    result = provider.segment(image=None, image_filename="CR_UnknownSite_T01_c999.JPG")

    assert result.image_width == 100
    assert result.image_height == 100


def test_provider_factory_uses_environment_setting(monkeypatch):
    monkeypatch.setenv("SEGMENTATION_PROVIDER", "fixture")
    provider = get_segmentation_provider()
    assert provider.__class__.__name__ == "FixtureProvider"


def test_provider_factory_falls_back_to_fixture_when_coral_scop_init_fails(monkeypatch):
    monkeypatch.setenv("SEGMENTATION_PROVIDER", "coralscop")

    import importlib
    import app.segmentation.provider_factory as provider_factory

    def failing_factory(*args, **kwargs):
        raise RuntimeError("Model unavailable")

    monkeypatch.setitem(sys.modules, "app.segmentation.coralscop_provider", type("Module", (), {"CoralScopProvider": failing_factory}))
    importlib.reload(provider_factory)
    provider = provider_factory.get_segmentation_provider()

    assert provider.__class__.__name__ == "FixtureProvider"


def test_provider_factory_rejects_unknown_setting(monkeypatch):
    monkeypatch.setenv("SEGMENTATION_PROVIDER", "unknown")
    try:
        get_segmentation_provider()
    except ValueError as exc:
        assert "Unsupported segmentation provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported segmentation provider")
