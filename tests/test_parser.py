"""Tests for the markdown to Notion blocks parser."""

from notion_md_cli.parser import parse_markdown


def test_title_extraction():
    title, blocks = parse_markdown("# My Document\n\nSome text.")
    assert title == "My Document"
    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"


def test_no_title():
    title, blocks = parse_markdown("Some text without heading.")
    assert title == ""
    assert len(blocks) == 1


def test_subsequent_h1_becomes_heading_1():
    title, blocks = parse_markdown("# First\n\n# Second\n")
    assert title == "First"
    assert blocks[0]["type"] == "heading_1"


def test_heading_levels():
    md = "# T\n\n## H2\n\n### H3\n\n#### H4\n\n##### H5\n"
    _, blocks = parse_markdown(md)
    assert blocks[0]["type"] == "heading_2"
    assert blocks[1]["type"] == "heading_3"
    # h4 and h5 become bold paragraphs
    assert blocks[2]["type"] == "paragraph"
    assert blocks[2]["paragraph"]["rich_text"][0]["annotations"]["bold"] is True
    assert blocks[3]["type"] == "paragraph"


def test_bold_italic_code_inline():
    _, blocks = parse_markdown("**bold** *italic* `code`\n")
    rt = blocks[0]["paragraph"]["rich_text"]
    texts = [(s["text"]["content"], s.get("annotations", {})) for s in rt]
    assert any(t == "bold" and a.get("bold") for t, a in texts)
    assert any(t == "italic" and a.get("italic") for t, a in texts)
    assert any(t == "code" and a.get("code") for t, a in texts)


def test_nested_bold_italic():
    _, blocks = parse_markdown("***bold and italic***\n")
    rt = blocks[0]["paragraph"]["rich_text"]
    for seg in rt:
        content = seg["text"]["content"].strip()
        if content:
            ann = seg.get("annotations", {})
            assert ann.get("bold") or ann.get("italic")


def test_link():
    _, blocks = parse_markdown("[click](https://example.com)\n")
    rt = blocks[0]["paragraph"]["rich_text"]
    link_segs = [s for s in rt if s["text"].get("link")]
    assert len(link_segs) >= 1
    assert link_segs[0]["text"]["link"]["url"] == "https://example.com"


def test_code_block():
    _, blocks = parse_markdown("```python\nx = 1\n```\n")
    assert blocks[0]["type"] == "code"
    assert blocks[0]["code"]["language"] == "python"
    assert "x = 1" in blocks[0]["code"]["rich_text"][0]["text"]["content"]


def test_code_block_unknown_language():
    _, blocks = parse_markdown("```unknownlang\nfoo\n```\n")
    assert blocks[0]["code"]["language"] == "plain text"


def test_code_block_no_language():
    _, blocks = parse_markdown("```\nfoo\n```\n")
    assert blocks[0]["code"]["language"] == "plain text"


def test_unordered_list():
    _, blocks = parse_markdown("- a\n- b\n- c\n")
    assert len(blocks) == 3
    for b in blocks:
        assert b["type"] == "bulleted_list_item"
    texts = [b["bulleted_list_item"]["rich_text"][0]["text"]["content"] for b in blocks]
    assert texts == ["a", "b", "c"]


def test_ordered_list():
    _, blocks = parse_markdown("1. first\n2. second\n")
    assert len(blocks) == 2
    for b in blocks:
        assert b["type"] == "numbered_list_item"


def test_nested_list():
    _, blocks = parse_markdown("- parent\n  - child\n")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "bulleted_list_item"
    children = blocks[0]["bulleted_list_item"]["children"]
    assert len(children) == 1
    assert children[0]["type"] == "bulleted_list_item"


def test_block_quote():
    _, blocks = parse_markdown("> quoted text\n")
    assert blocks[0]["type"] == "quote"
    assert blocks[0]["quote"]["rich_text"][0]["text"]["content"] == "quoted text"


def test_thematic_break():
    _, blocks = parse_markdown("---\n")
    assert blocks[0]["type"] == "divider"


def test_table():
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n"
    _, blocks = parse_markdown(md)
    assert blocks[0]["type"] == "table"
    table = blocks[0]["table"]
    assert table["table_width"] == 2
    assert table["has_column_header"] is True
    assert len(table["children"]) == 3  # header + 2 body rows


def test_blank_lines_skipped():
    _, blocks = parse_markdown("\n\n\nHello\n\n\n")
    assert len(blocks) == 1


def test_chunk_rich_text():
    from notion_md_cli.parser import _chunk_rich_text

    long_text = "x" * 5000
    segments = [{"type": "text", "text": {"content": long_text}}]
    chunked = _chunk_rich_text(segments, limit=2000)
    assert len(chunked) == 3
    assert all(len(s["text"]["content"]) <= 2000 for s in chunked)
    recombined = "".join(s["text"]["content"] for s in chunked)
    assert recombined == long_text


def test_full_document():
    md = """# My Document

Some **bold** and *italic* text with `code`.

## Section 1

A paragraph with a [link](https://example.com).

- item 1
- item 2
  - nested item
- item 3

### Subsection

```python
def hello():
    print("world")
```

> A block quote

---

| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |

1. first
2. second
3. third
"""
    title, blocks = parse_markdown(md)
    assert title == "My Document"
    assert len(blocks) == 14

    types = [b["type"] for b in blocks]
    assert types == [
        "paragraph",
        "heading_2",
        "paragraph",
        "bulleted_list_item",
        "bulleted_list_item",
        "bulleted_list_item",
        "heading_3",
        "code",
        "quote",
        "divider",
        "table",
        "numbered_list_item",
        "numbered_list_item",
        "numbered_list_item",
    ]
