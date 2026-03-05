"""Markdown to Notion blocks converter using mistune v3 AST mode."""

from typing import Any

import mistune

# Type alias for mistune AST nodes (dicts with "type", "children", etc.)
ASTNode = dict[str, Any]

NOTION_LANGUAGES = {
    "abap",
    "arduino",
    "bash",
    "basic",
    "c",
    "clojure",
    "coffeescript",
    "c++",
    "c#",
    "css",
    "dart",
    "diff",
    "docker",
    "elixir",
    "elm",
    "erlang",
    "flow",
    "fortran",
    "f#",
    "gherkin",
    "glsl",
    "go",
    "graphql",
    "groovy",
    "haskell",
    "html",
    "java",
    "javascript",
    "json",
    "julia",
    "kotlin",
    "latex",
    "less",
    "lisp",
    "livescript",
    "lua",
    "makefile",
    "markdown",
    "markup",
    "matlab",
    "mermaid",
    "nix",
    "objective-c",
    "ocaml",
    "pascal",
    "perl",
    "php",
    "plain text",
    "powershell",
    "prolog",
    "protobuf",
    "python",
    "r",
    "reason",
    "ruby",
    "rust",
    "sass",
    "scala",
    "scheme",
    "scss",
    "shell",
    "sql",
    "swift",
    "typescript",
    "vb.net",
    "verilog",
    "vhdl",
    "visual basic",
    "webassembly",
    "xml",
    "yaml",
    "java/c/c++/c#",
    "toml",
}


def parse_markdown(md_text: str) -> tuple[str, list[dict]]:
    """Parse markdown text into a title and list of Notion blocks.

    Args:
        md_text: Raw markdown string.

    Returns:
        A tuple of (title, blocks) where title is extracted from the first H1
        heading and blocks is a list of Notion block dicts.
    """
    md = mistune.create_markdown(renderer="ast", plugins=["table"])
    raw_ast = md(md_text)

    title = ""
    blocks: list[dict[str, Any]] = []

    for raw_node in raw_ast:
        if not isinstance(raw_node, dict):
            continue
        node: ASTNode = raw_node
        node_type = node.get("type", "")

        if node_type == "heading":
            level = node["attrs"]["level"]
            if level == 1 and not title:
                title = _plain_text(node.get("children", []))
                continue
            blocks.extend(_convert_heading(node))

        elif node_type == "paragraph":
            blocks.extend(_convert_paragraph(node))

        elif node_type == "block_code":
            blocks.append(_convert_code_block(node))

        elif node_type == "block_quote":
            blocks.extend(_convert_block_quote(node))

        elif node_type == "list":
            blocks.extend(_convert_list(node))

        elif node_type == "thematic_break":
            blocks.append({"type": "divider", "divider": {}})

        elif node_type == "table":
            blocks.append(_convert_table(node))

        elif node_type == "blank_line":
            continue

    return title, blocks


def _plain_text(children: list[ASTNode]) -> str:
    """Extract plain text from inline AST nodes."""
    parts: list[str] = []
    for child in children:
        t = child.get("type", "")
        if t == "text":
            parts.append(child.get("raw", "") or child.get("children", ""))
        elif t == "codespan":
            parts.append(child.get("raw", "") or child.get("children", ""))
        elif t == "softbreak":
            parts.append("\n")
        elif t in ("strong", "emphasis", "link"):
            parts.append(_plain_text(child.get("children", [])))
    return "".join(parts)


def _render_inline(children: list[ASTNode], annotations: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Walk inline AST nodes and produce Notion rich_text segments.

    Args:
        children: List of inline AST nodes from mistune.
        annotations: Current annotation state to apply.

    Returns:
        List of Notion rich_text segment dicts.
    """
    if annotations is None:
        annotations = {}

    segments: list[dict[str, Any]] = []

    for child in children:
        t = child.get("type", "")

        if t == "text":
            raw = child.get("raw", "") or child.get("children", "")
            seg = _make_text_segment(raw, annotations)
            segments.append(seg)

        elif t == "strong":
            inner = _render_inline(child.get("children", []), {**annotations, "bold": True})
            segments.extend(inner)

        elif t == "emphasis":
            inner = _render_inline(child.get("children", []), {**annotations, "italic": True})
            segments.extend(inner)

        elif t == "codespan":
            raw = child.get("raw", "") or child.get("children", "")
            seg = _make_text_segment(raw, {**annotations, "code": True})
            segments.append(seg)

        elif t == "link":
            url = child.get("attrs", {}).get("url", "")
            inner = _render_inline(child.get("children", []), annotations)
            for s in inner:
                s["text"]["link"] = {"url": url}
            segments.extend(inner)

        elif t == "softbreak":
            seg = _make_text_segment("\n", annotations)
            segments.append(seg)

        elif t == "strikethrough":
            inner = _render_inline(
                child.get("children", []),
                {**annotations, "strikethrough": True},
            )
            segments.extend(inner)

    return segments


def _make_text_segment(content: str, annotations: dict[str, Any]) -> dict[str, Any]:
    """Create a single Notion rich_text segment."""
    seg: dict[str, Any] = {
        "type": "text",
        "text": {"content": content},
    }
    filtered = {
        k: v
        for k, v in annotations.items()
        if k in ("bold", "italic", "strikethrough", "underline", "code", "color") and v
    }
    if filtered:
        seg["annotations"] = filtered
    return seg


def _chunk_rich_text(segments: list[dict[str, Any]], limit: int = 2000) -> list[dict[str, Any]]:
    """Split rich_text segments so no single segment exceeds the char limit.

    Args:
        segments: List of Notion rich_text segments.
        limit: Maximum characters per segment.

    Returns:
        New list of segments with long ones split.
    """
    result: list[dict[str, Any]] = []
    for seg in segments:
        content = seg["text"]["content"]
        if len(content) <= limit:
            result.append(seg)
            continue
        for i in range(0, len(content), limit):
            chunk = dict(seg)
            chunk["text"] = {**seg["text"], "content": content[i : i + limit]}
            result.append(chunk)
    return result


def _convert_heading(node: ASTNode) -> list[dict[str, Any]]:
    """Convert a heading node to Notion block(s)."""
    level = node["attrs"]["level"]
    rich_text = _chunk_rich_text(_render_inline(node.get("children", [])))

    if level == 1:
        return [{"type": "heading_1", "heading_1": {"rich_text": rich_text}}]
    elif level == 2:
        return [{"type": "heading_2", "heading_2": {"rich_text": rich_text}}]
    elif level == 3:
        return [{"type": "heading_3", "heading_3": {"rich_text": rich_text}}]
    else:
        for seg in rich_text:
            seg.setdefault("annotations", {})["bold"] = True
        return [{"type": "paragraph", "paragraph": {"rich_text": rich_text}}]


def _convert_paragraph(node: ASTNode) -> list[dict[str, Any]]:
    """Convert a paragraph node to a Notion paragraph block."""
    rich_text = _chunk_rich_text(_render_inline(node.get("children", [])))
    return [{"type": "paragraph", "paragraph": {"rich_text": rich_text}}]


def _convert_code_block(node: ASTNode) -> dict[str, Any]:
    """Convert a code block node to a Notion code block."""
    raw = node.get("raw", "") or node.get("children", [{}])[0].get("raw", "")
    info = node.get("attrs", {}).get("info", "") or ""
    lang = info.strip().lower() if info else "plain text"
    if lang not in NOTION_LANGUAGES:
        lang = "plain text"

    rich_text = _chunk_rich_text([{"type": "text", "text": {"content": raw}}])
    return {
        "type": "code",
        "code": {"rich_text": rich_text, "language": lang},
    }


def _convert_block_quote(node: ASTNode) -> list[dict[str, Any]]:
    """Convert a block_quote node to Notion quote blocks."""
    blocks: list[dict[str, Any]] = []
    for child in node.get("children", []):
        if child.get("type") == "paragraph":
            rich_text = _chunk_rich_text(_render_inline(child.get("children", [])))
            blocks.append({"type": "quote", "quote": {"rich_text": rich_text}})
    return blocks


def _convert_list(node: ASTNode) -> list[dict[str, Any]]:
    """Convert a list node to Notion list item blocks."""
    ordered = node.get("attrs", {}).get("ordered", False)
    block_type = "numbered_list_item" if ordered else "bulleted_list_item"
    blocks: list[dict[str, Any]] = []

    for item in node.get("children", []):
        if item.get("type") != "list_item":
            continue
        block = _convert_list_item(item, block_type)
        blocks.append(block)

    return blocks


def _convert_list_item(item: ASTNode, block_type: str) -> dict[str, Any]:
    """Convert a single list_item node to a Notion list item block.

    Args:
        item: The list_item AST node.
        block_type: Either 'bulleted_list_item' or 'numbered_list_item'.

    Returns:
        A Notion block dict, potentially with nested children.
    """
    rich_text_parts: list[dict[str, Any]] = []
    children_blocks: list[dict[str, Any]] = []

    for child in item.get("children", []):
        child_type = child.get("type", "")
        if child_type in ("paragraph", "block_text"):
            rich_text_parts.extend(_render_inline(child.get("children", [])))
        elif child_type == "list":
            nested = _convert_list(child)
            children_blocks.extend(nested)
        elif child_type == "block_code":
            children_blocks.append(_convert_code_block(child))
        elif child_type == "block_quote":
            children_blocks.extend(_convert_block_quote(child))

    rich_text = _chunk_rich_text(rich_text_parts)
    block: dict[str, Any] = {
        "type": block_type,
        block_type: {"rich_text": rich_text},
    }
    if children_blocks:
        block[block_type]["children"] = children_blocks

    return block


def _convert_table(node: ASTNode) -> dict[str, Any]:
    """Convert a table node to a Notion table block."""
    rows: list[dict[str, Any]] = []
    table_width = 0

    for section in node.get("children", []):
        section_type = section.get("type", "")
        if section_type == "table_head":
            # table_head contains cells directly (no table_row wrapper)
            cells: list[list[dict[str, Any]]] = []
            for cell_node in section.get("children", []):
                if cell_node.get("type") != "table_cell":
                    continue
                cell_rt = _chunk_rich_text(_render_inline(cell_node.get("children", [])))
                cells.append(cell_rt)
            table_width = max(table_width, len(cells))
            rows.append({"type": "table_row", "table_row": {"cells": cells}})
        elif section_type == "table_body":
            for row_node in section.get("children", []):
                if row_node.get("type") != "table_row":
                    continue
                cells = []
                for cell_node in row_node.get("children", []):
                    if cell_node.get("type") != "table_cell":
                        continue
                    cell_rt = _chunk_rich_text(_render_inline(cell_node.get("children", [])))
                    cells.append(cell_rt)
                table_width = max(table_width, len(cells))
                rows.append({"type": "table_row", "table_row": {"cells": cells}})

    return {
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": True,
            "has_row_header": False,
            "children": rows,
        },
    }
