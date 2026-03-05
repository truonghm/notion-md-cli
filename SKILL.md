---
name: notion-md-cli
description: Push markdown files to Notion as pages and pull Notion pages as plain text using the notion-md-cli command. Use when the user wants to publish documentation to Notion, read Notion page content, or search their Notion workspace from the terminal.
allowed-tools: Bash(notion-md-cli *)
---

# notion-md-cli

CLI tool for pushing markdown files to Notion and pulling Notion pages as plain text. One-way publishing only - no sync, no images, no deduplication.

## Prerequisites

- `notion-md-cli` is installed globally and available on `PATH`
- `NOTION_API_KEY` environment variable is set

## Page identifiers

Anywhere a page ID is required, you can pass any of:

- A bare page ID: `abcdef1234567890abcdef1234567890`
- A dashed UUID: `31a9bacd-d84a-80f9-8f4f-d02f03f84318`
- A full Notion URL: `https://www.notion.so/workspace/Page-Title-abcdef1234567890abcdef1234567890`

The CLI extracts the ID automatically.

## Commands

### `push` - Push a markdown file to Notion

Creates a new Notion page as a child of the specified parent page.

```bash
notion-md-cli push <file> --parent <page_id_or_url> [--title <title>]
```

| Parameter  | Required | Description                                                                                                                |
| ---------- | -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `file`     | Yes      | Path to the markdown file.                                                                                                 |
| `--parent` | Yes      | Page ID or URL of the parent page. The new page is created as a child.                                                     |
| `--title`  | No       | Override page title. Default: first `# H1` in the file, or filename if no H1.                                              |

Prints the URL of the created page to stdout.

**Supported markdown features:**

- Headings (H1-H5; H4/H5 rendered as bold paragraphs)
- Bold, italic, inline code
- Links
- Ordered and unordered lists (with nesting)
- Code blocks (with language detection)
- Block quotes
- Tables
- Horizontal rules

**Examples:**

```bash
# Push a file, title comes from the first H1 heading
notion-md-cli push docs/architecture.md --parent abcdef1234567890abcdef1234567890

# Push with a custom title
notion-md-cli push notes.md --parent abcdef1234567890abcdef1234567890 --title "Sprint 42 Notes"

# Use a full Notion URL as the parent
notion-md-cli push README.md --parent "https://www.notion.so/Engineering-abcdef1234567890abcdef1234567890"
```

### `pull` - Pull a Notion page as plain text

Fetches a Notion page and all its blocks recursively, then outputs plain text to stdout. The page title is printed as an H1 heading at the top.

```bash
notion-md-cli pull <page_id_or_url>
```

| Parameter | Required | Description                         |
| --------- | -------- | ----------------------------------- |
| `page_id` | Yes      | Page ID or URL of the page to pull. |

**Examples:**

```bash
# Pull a page and print to stdout
notion-md-cli pull abcdef1234567890abcdef1234567890

# Pull using a full URL
notion-md-cli pull "https://www.notion.so/My-Page-abcdef1234567890abcdef1234567890"

# Save to a file
notion-md-cli pull abcdef1234567890abcdef1234567890 > output.md

# Pipe to another tool
notion-md-cli pull abcdef1234567890abcdef1234567890 | grep "TODO"
```

### `list` - Search Notion pages

Searches your workspace for pages matching a query. With no query, lists all pages the integration can access. Outputs one line per page: title, ID, and URL.

```bash
notion-md-cli list [query]
```

| Parameter | Required | Description                                                      |
| --------- | -------- | ---------------------------------------------------------------- |
| `query`   | No       | Search string. Matches page titles. Omit to list all accessible. |

**Examples:**

```bash
# List all pages the integration can see
notion-md-cli list

# Search for pages with "roadmap" in the title
notion-md-cli list "roadmap"

# Search and grab just the page IDs
notion-md-cli list "meeting notes" | awk '{print $NF}'
```

## Notes for agents

- Every `push` creates a new page. There is no update/overwrite - pushing the same file twice creates duplicate pages.
- `pull` output is plain text, not markdown. Formatting (bold, italic, etc.) is stripped. Use it for reading content, not for round-tripping back to Notion.
- The `--parent` for `push` must be a page the integration already has access to. If you get a 403, the integration has not been granted access to that page.
- All commands read `NOTION_API_KEY` from the environment. You do not need to pass `--api-key` if the env var is set.
