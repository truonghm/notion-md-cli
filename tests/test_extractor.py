"""Tests for the Notion blocks to plain text extractor."""

from notion_md_cli.extractor import extract_text


def _rt(text: str) -> list[dict]:
    """Helper to create a rich_text array with plain_text."""
    return [{"plain_text": text}]


def test_heading_levels():
    blocks = [
        {"type": "heading_1", "heading_1": {"rich_text": _rt("H1")}},
        {"type": "heading_2", "heading_2": {"rich_text": _rt("H2")}},
        {"type": "heading_3", "heading_3": {"rich_text": _rt("H3")}},
    ]
    result = extract_text(blocks)
    assert "# H1" in result
    assert "## H2" in result
    assert "### H3" in result


def test_paragraph():
    blocks = [{"type": "paragraph", "paragraph": {"rich_text": _rt("Hello world")}}]
    assert "Hello world" in extract_text(blocks)


def test_code_block():
    blocks = [
        {
            "type": "code",
            "code": {"rich_text": _rt("x = 1"), "language": "python"},
        }
    ]
    result = extract_text(blocks)
    assert "```python" in result
    assert "x = 1" in result
    assert "```" in result


def test_bulleted_list():
    blocks = [
        {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _rt("item 1")}},
        {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _rt("item 2")}},
    ]
    result = extract_text(blocks)
    assert "- item 1" in result
    assert "- item 2" in result


def test_numbered_list():
    blocks = [
        {"type": "numbered_list_item", "numbered_list_item": {"rich_text": _rt("first")}},
        {"type": "numbered_list_item", "numbered_list_item": {"rich_text": _rt("second")}},
    ]
    result = extract_text(blocks)
    assert "1. first" in result
    assert "1. second" in result


def test_nested_list():
    blocks = [
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": _rt("parent"),
                "children": [
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": _rt("child")},
                    }
                ],
            },
        }
    ]
    result = extract_text(blocks)
    assert "- parent" in result
    assert "  - child" in result


def test_quote():
    blocks = [{"type": "quote", "quote": {"rich_text": _rt("quoted")}}]
    assert "> quoted" in extract_text(blocks)


def test_divider():
    blocks = [{"type": "divider", "divider": {}}]
    assert "---" in extract_text(blocks)


def test_table():
    blocks = [
        {
            "type": "table",
            "table": {
                "children": [
                    {
                        "type": "table_row",
                        "table_row": {"cells": [_rt("A"), _rt("B")]},
                    },
                    {
                        "type": "table_row",
                        "table_row": {"cells": [_rt("1"), _rt("2")]},
                    },
                ]
            },
        }
    ]
    result = extract_text(blocks)
    assert "| A | B |" in result
    assert "| 1 | 2 |" in result


def test_unknown_block_type():
    blocks = [{"type": "bookmark", "bookmark": {"url": "https://example.com"}}]
    result = extract_text(blocks)
    assert "[bookmark block]" in result


def test_roundtrip_with_parser():
    """Parse markdown, add plain_text fields, extract back to text."""
    from notion_md_cli.parser import parse_markdown

    md = """# Title

Hello **world**.

- item 1
- item 2

```python
x = 1
```

> quote

---
"""
    title, blocks = parse_markdown(md)

    def add_plain_text(block_list: list[dict]) -> None:
        for b in block_list:
            bt = b["type"]
            data = b.get(bt, {})
            for seg in data.get("rich_text", []):
                seg["plain_text"] = seg["text"]["content"]
            for child in data.get("children", []):
                add_plain_text([child])

    add_plain_text(blocks)
    result = extract_text(blocks)

    assert "Hello" in result
    assert "world" in result
    assert "- item 1" in result
    assert "```python" in result
    assert "> quote" in result
    assert "---" in result
