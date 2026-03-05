"""Notion blocks to plain text converter."""


def extract_text(blocks: list[dict], indent: int = 0) -> str:
    """Convert a list of Notion blocks to plain text.

    Args:
        blocks: List of Notion block dicts (as returned by the API).
        indent: Current indentation level for nested list items.

    Returns:
        Plain text representation of the blocks.
    """
    parts: list[str] = []
    prefix = "  " * indent

    for block in blocks:
        block_type = block.get("type", "")
        data = block.get(block_type, {})

        if block_type in ("heading_1", "heading_2", "heading_3"):
            level = int(block_type[-1])
            text = _rich_text_to_str(data.get("rich_text", []))
            parts.append(f"{'#' * level} {text}\n\n")

        elif block_type == "paragraph":
            text = _rich_text_to_str(data.get("rich_text", []))
            parts.append(f"{prefix}{text}\n\n")

        elif block_type == "code":
            lang = data.get("language", "")
            code = _rich_text_to_str(data.get("rich_text", []))
            parts.append(f"{prefix}```{lang}\n{code}\n```\n\n")

        elif block_type == "bulleted_list_item":
            text = _rich_text_to_str(data.get("rich_text", []))
            parts.append(f"{prefix}- {text}\n")
            children = data.get("children") or block.get("children", [])
            if children:
                parts.append(extract_text(children, indent + 1))

        elif block_type == "numbered_list_item":
            text = _rich_text_to_str(data.get("rich_text", []))
            parts.append(f"{prefix}1. {text}\n")
            children = data.get("children") or block.get("children", [])
            if children:
                parts.append(extract_text(children, indent + 1))

        elif block_type == "quote":
            text = _rich_text_to_str(data.get("rich_text", []))
            parts.append(f"{prefix}> {text}\n\n")

        elif block_type == "divider":
            parts.append(f"{prefix}---\n\n")

        elif block_type == "table":
            rows = data.get("children") or block.get("children", [])
            parts.append(_render_table(rows, prefix))

        else:
            parts.append(f"{prefix}[{block_type} block]\n\n")

    return "".join(parts)


def _rich_text_to_str(rich_text: list[dict]) -> str:
    """Concatenate plain_text fields from Notion rich_text segments.

    Args:
        rich_text: List of Notion rich_text objects.

    Returns:
        Combined plain text string.
    """
    return "".join(seg.get("plain_text", "") for seg in rich_text)


def _render_table(rows: list[dict], prefix: str = "") -> str:
    """Render table rows as pipe-separated plain text.

    Args:
        rows: List of table_row block dicts.
        prefix: Indentation prefix.

    Returns:
        Pipe-separated table string.
    """
    lines: list[str] = []
    for i, row in enumerate(rows):
        row_data = row.get("table_row", {})
        cells = row_data.get("cells", [])
        cell_texts = [_rich_text_to_str(cell) for cell in cells]
        lines.append(f"{prefix}| {' | '.join(cell_texts)} |")
        if i == 0:
            sep = ["-" * max(len(t), 3) for t in cell_texts]
            lines.append(f"{prefix}| {' | '.join(sep)} |")
    if lines:
        return "\n".join(lines) + "\n\n"
    return ""
