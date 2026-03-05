"""CLI interface for notion-md-cli."""

import os
import re
from pathlib import Path

import typer

from notion_md_cli.client import NotionClient
from notion_md_cli.extractor import extract_text
from notion_md_cli.parser import parse_markdown

app = typer.Typer(help="Use Notion as markdown storage.")

NOTION_ID_RE = re.compile(r"[a-f0-9]{32}|[a-f0-9\-]{36}")


def _normalize_page_id(raw: str) -> str:
    """Extract a Notion page ID from a URL or raw ID string.

    Args:
        raw: A Notion page URL or bare page ID.

    Returns:
        The extracted 32-char hex ID or the input stripped of dashes.

    Raises:
        typer.BadParameter: If no valid ID could be extracted.
    """
    match = NOTION_ID_RE.search(raw)
    if match:
        return match.group(0).replace("-", "")
    raise typer.BadParameter(f"Could not extract a Notion page ID from: {raw}")


def _get_client(api_key: str | None) -> NotionClient:
    """Resolve API key and create a NotionClient.

    Args:
        api_key: Explicit API key, or None to read from env.

    Returns:
        A configured NotionClient.

    Raises:
        typer.BadParameter: If no API key is available.
    """
    key = api_key or os.environ.get("NOTION_API_KEY", "")
    if not key:
        raise typer.BadParameter("Provide --api-key or set NOTION_API_KEY env var.")
    return NotionClient(key)


@app.command()
def push(
    file: Path = typer.Argument(..., help="Markdown file to push."),
    parent: str = typer.Option(..., help="Parent page ID or URL."),
    title: str | None = typer.Option(None, help="Override page title (default: first H1 or filename)."),
    api_key: str | None = typer.Option(None, "--api-key", envvar="NOTION_API_KEY", help="Notion API key."),
) -> None:
    """Push a markdown file as a new Notion page."""
    if not file.is_file():
        typer.echo(f"Error: {file} is not a file.", err=True)
        raise typer.Exit(1)

    md_text = file.read_text(encoding="utf-8")
    parsed_title, blocks = parse_markdown(md_text)
    page_title = title or parsed_title or file.stem

    client = _get_client(api_key)
    parent_id = _normalize_page_id(parent)
    result = client.create_page(parent_id, page_title, blocks)

    typer.echo(f"Created: {result['url']}")


@app.command()
def pull(
    page_id: str = typer.Argument(..., help="Notion page ID or URL."),
    api_key: str | None = typer.Option(None, "--api-key", envvar="NOTION_API_KEY", help="Notion API key."),
) -> None:
    """Pull a Notion page as plain text."""
    client = _get_client(api_key)
    pid = _normalize_page_id(page_id)

    page = client.fetch_page(pid)
    blocks = client.fetch_blocks(pid)
    text = extract_text(blocks)

    header = f"# {page['title']}\n\n" if page["title"] else ""
    typer.echo(header + text, nl=False)


@app.command(name="list")
def list_pages(
    query: str = typer.Argument("", help="Search query."),
    api_key: str | None = typer.Option(None, "--api-key", envvar="NOTION_API_KEY", help="Notion API key."),
) -> None:
    """List/search Notion pages."""
    client = _get_client(api_key)
    pages = client.search_pages(query)

    if not pages:
        typer.echo("No pages found.")
        return

    for page in pages:
        typer.echo(f"{page['title']:<50} {page['id']}  {page['url']}")
