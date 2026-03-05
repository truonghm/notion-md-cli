"""Notion API wrapper for page creation and retrieval."""

from typing import Any, cast

from notion_client import Client
from notion_client.helpers import collect_paginated_api


class NotionClient:
    """Thin wrapper around the Notion SDK for page and block operations.

    Args:
        api_key: Notion integration token.
    """

    def __init__(self, api_key: str) -> None:
        self._client = Client(auth=api_key)

    def create_page(self, parent_id: str, title: str, blocks: list[dict]) -> dict:
        """Create a new Notion page with the given title and blocks.

        Args:
            parent_id: The ID of the parent page.
            title: Page title.
            blocks: List of Notion block dicts.

        Returns:
            Dict with 'id' and 'url' of the created page.
        """
        first_batch = blocks[:100]
        remaining = blocks[100:]

        page: dict[str, Any] = cast(
            dict[str, Any],
            self._client.pages.create(
                parent={"page_id": parent_id},
                properties={"title": [{"type": "text", "text": {"content": title}}]},
                children=first_batch,
            ),
        )

        if remaining:
            self._append_blocks(page["id"], remaining)

        return {"id": page["id"], "url": page["url"]}

    def _append_blocks(self, block_id: str, blocks: list[dict]) -> None:
        """Append blocks to an existing block, handling batching and nesting.

        Notion limits appends to 100 blocks per request and 2 levels of nesting
        depth per request. This method strips deeper children and appends them
        in follow-up calls.

        Args:
            block_id: The block/page ID to append to.
            blocks: List of Notion block dicts to append.
        """
        for i in range(0, len(blocks), 100):
            batch = blocks[i : i + 100]
            stripped, deferred = _strip_deep_children(batch, max_depth=2)

            result: dict[str, Any] = cast(
                dict[str, Any],
                self._client.blocks.children.append(block_id=block_id, children=stripped),
            )

            if deferred:
                returned_blocks = result.get("results", [])
                for idx, children in deferred.items():
                    if idx < len(returned_blocks):
                        self._append_blocks(returned_blocks[idx]["id"], children)

    def fetch_page(self, page_id: str) -> dict:
        """Fetch page properties.

        Args:
            page_id: The Notion page ID.

        Returns:
            Dict with 'id', 'title', and 'url'.
        """
        page: dict[str, Any] = cast(dict[str, Any], self._client.pages.retrieve(page_id=page_id))
        title = ""
        title_prop = page.get("properties", {}).get("title", {})
        if title_prop.get("title"):
            title = "".join(t.get("plain_text", "") for t in title_prop["title"])
        return {"id": page["id"], "title": title, "url": page["url"]}

    def fetch_blocks(self, block_id: str) -> list[dict]:
        """Recursively fetch all blocks for a page or block.

        Args:
            block_id: The page or block ID.

        Returns:
            List of block dicts with children recursively attached.
        """
        blocks: list[dict[str, Any]] = cast(
            list[dict[str, Any]],
            collect_paginated_api(self._client.blocks.children.list, block_id=block_id),
        )
        for block in blocks:
            if block.get("has_children"):
                block["children"] = self.fetch_blocks(block["id"])
        return blocks

    def search_pages(self, query: str = "") -> list[dict]:
        """Search for pages by title.

        Args:
            query: Search query string.

        Returns:
            List of dicts with 'id', 'title', and 'url'.
        """
        response: dict[str, Any] = cast(
            dict[str, Any],
            self._client.search(
                query=query,
                filter={"property": "object", "value": "page"},
            ),
        )
        results = response.get("results", [])

        pages: list[dict] = []
        for page in results:
            title = ""
            title_prop = page.get("properties", {}).get("title", {})
            if title_prop.get("title"):
                title = "".join(t.get("plain_text", "") for t in title_prop["title"])
            pages.append({"id": page["id"], "title": title, "url": page["url"]})
        return pages


def _strip_deep_children(
    blocks: list[dict], max_depth: int, current_depth: int = 1
) -> tuple[list[dict], dict[int, list[dict]]]:
    """Strip children deeper than max_depth from blocks.

    Args:
        blocks: List of Notion block dicts.
        max_depth: Maximum nesting depth to keep.
        current_depth: Current depth in the tree.

    Returns:
        A tuple of (stripped_blocks, deferred) where deferred maps block
        indices to their stripped children for later appending.
    """
    stripped: list[dict] = []
    deferred: dict[int, list[dict]] = {}

    for i, block in enumerate(blocks):
        block_type = block.get("type", "")
        data = block.get(block_type, {})
        children = data.get("children")

        if children is None:
            stripped.append(block)
            continue

        new_block = {**block, block_type: {**data}}

        if current_depth >= max_depth:
            new_block[block_type] = {k: v for k, v in data.items() if k != "children"}
            deferred[i] = children
        else:
            sub_stripped, sub_deferred = _strip_deep_children(children, max_depth, current_depth + 1)
            new_block[block_type] = {**data, "children": sub_stripped}
            if sub_deferred:
                pass

        stripped.append(new_block)

    return stripped, deferred
