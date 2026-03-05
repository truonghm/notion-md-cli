# Notion Markdown CLI

A CLI tool for using Notion as markdown storage. Push markdown files as Notion pages and pull Notion pages back as plain text. Designed for one-way publishing - not a sync tool. No image handling, no deduplication, no in-place editing.

Useful for:

- Publishing documentation or notes to Notion from a local repo
- Pulling Notion page content as plain text for coding agents or scripts
- Searching your Notion workspace from the terminal

This tool can also be used as an agent skill (e.g. for Claude Code). See [SKILL.md](SKILL.md) for an example skill file.

## Installation

```bash
uv tool install git+https://github.com/truonghm/notion-md-cli
```

This installs `notion-md-cli` as a globally available command.

To upgrade to the latest version:

```bash
uv tool upgrade notion-md-cli
```

## Setting up

### 1. Create a Notion integration

1. Go to <https://www.notion.so/my-integrations>
2. Click "New integration"
3. Give it a name, select a workspace, and click Submit
4. Copy the token (starts with `ntn_` or `secret_`)

The integration needs **Read content**, **Update content**, and **Insert content** capabilities (these are the defaults when creating a new integration).

### 2. Grant the integration access

1. On the integration page, go to the **Access** tab
2. Click **Edit Access**
3. Choose a teamspace or private space, then select either the entire space or individual pages

Alternatively, you can connect the integration from within Notion on any page via the `...` menu (top right) -> "Connections".

### 3. Set your API key

Either export it as an environment variable (recommended):

```bash
export NOTION_API_KEY="ntn_..."
```

Or pass it explicitly with `--api-key` on every command:

```bash
notion-md-cli push myfile.md --parent <page_id> --api-key "ntn_..."
```

## Usage

### Page identifiers

Anywhere a page ID is required, you can provide either:

- A **bare page ID**: `abcdef1234567890abcdef1234567890`
- A **dashed UUID**: `31a9bacd-d84a-80f9-8f4f-d02f03f84318`
- A **full Notion URL**: `https://www.notion.so/workspace/Page-Title-abcdef1234567890abcdef1234567890`

The CLI extracts the ID automatically.

### `push` - Push a markdown file to Notion

Creates a new Notion page as a child of the specified parent page.

```bash
notion-md-cli push <file> --parent <page_id_or_url> [--title <title>] [--api-key <key>]
```

**Parameters:**

| Parameter   | Required | Description                                                                                                                                                         |
| ----------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `file`      | Yes      | Path to the markdown file to push.                                                                                                                                  |
| `--parent`  | Yes      | Page ID or URL of the parent page. The new page is created as a child of this page.                                                                                 |
| `--title`   | No       | Override the page title. By default, the title is extracted from the first `# H1` heading in the file. If there is no H1, the filename (without extension) is used. |
| `--api-key` | No       | Notion API key. Falls back to `NOTION_API_KEY` env var.                                                                                                             |

**Examples:**

```bash
# Push a file, title comes from the first H1 heading
notion-md-cli push docs/architecture.md --parent abcdef1234567890abcdef1234567890

# Push with a custom title
notion-md-cli push notes.md --parent abcdef1234567890abcdef1234567890 --title "Sprint 42 Notes"

# Use a full Notion URL as the parent
notion-md-cli push README.md --parent "https://www.notion.so/Engineering-abcdef1234567890abcdef1234567890"
```

**Supported markdown features:**

- Headings (H1-H5; H4/H5 rendered as bold paragraphs)
- Bold, italic, inline code
- Links
- Ordered and unordered lists (with nesting)
- Code blocks (with language detection)
- Block quotes
- Tables
- Horizontal rules

### `pull` - Pull a Notion page as plain text

Fetches a Notion page and all its blocks recursively, then outputs plain text to stdout. The page title is printed as an H1 heading at the top.

```bash
notion-md-cli pull <page_id_or_url> [--api-key <key>]
```

**Parameters:**

| Parameter   | Required | Description                                             |
| ----------- | -------- | ------------------------------------------------------- |
| `page_id`   | Yes      | Page ID or URL of the page to pull.                     |
| `--api-key` | No       | Notion API key. Falls back to `NOTION_API_KEY` env var. |

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

Searches your workspace for pages matching a query. With no query, lists all pages the integration can access. Outputs a table of title, ID, and URL.

```bash
notion-md-cli list [query] [--api-key <key>]
```

**Parameters:**

| Parameter   | Required | Description                                                                          |
| ----------- | -------- | ------------------------------------------------------------------------------------ |
| `query`     | No       | Search query string. Matches against page titles. Omit to list all accessible pages. |
| `--api-key` | No       | Notion API key. Falls back to `NOTION_API_KEY` env var.                              |

**Examples:**

```bash
# List all pages the integration can see
notion-md-cli list

# Search for pages with "roadmap" in the title
notion-md-cli list "roadmap"

# Search and grab just the page IDs
notion-md-cli list "meeting notes" | awk '{print $NF}'
```

## Development

Install:

- ruf
- prek
- pyrefly
- pytest
- pytest-cov

Setting up prek for pre-commit:

```bash
uv run prek install
```

Current test coverage:

```raw
$ uv run pytest --cov=src

Name                             Stmts   Miss  Cover
----------------------------------------------------
src/notion_md_cli/__init__.py        0      0   100%
src/notion_md_cli/cli.py            49     28    43%
src/notion_md_cli/client.py         67     56    16%
src/notion_md_cli/extractor.py      54      2    96%
src/notion_md_cli/parser.py        185     21    89%
----------------------------------------------------
TOTAL                              355    107    70%
```
