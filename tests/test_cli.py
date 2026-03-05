"""Tests for CLI argument handling and page ID normalization."""

import pytest
import typer

from notion_md_cli.cli import _normalize_page_id


def test_normalize_bare_id():
    raw = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
    assert _normalize_page_id(raw) == raw


def test_normalize_dashed_id():
    raw = "a1b2c3d4-e5f6-a1b2-c3d4-e5f6a1b2c3d4"
    assert _normalize_page_id(raw) == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"


def test_normalize_from_url():
    url = "https://www.notion.so/workspace/Page-Title-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
    assert _normalize_page_id(url) == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"


def test_normalize_invalid():
    with pytest.raises(typer.BadParameter):
        _normalize_page_id("not-a-valid-id")


def test_normalize_url_with_query_params():
    url = "https://www.notion.so/a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4?v=xyz"
    assert _normalize_page_id(url) == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
