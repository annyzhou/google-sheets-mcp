# google-sheets-mcp

A Google Sheets MCP server using OAuth2 bearer token auth via the Dedalus MCP framework.

## Tools

### Spreadsheets
- `sheets_get_spreadsheet` - Get spreadsheet metadata including title, locale, sheets, and named ranges
- `sheets_list_sheets` - List all sheets/tabs in a spreadsheet with their properties (ID, title, index, grid size)
- `sheets_create` - Create a new spreadsheet with optional title and sheets
- `sheets_batch_update` - Execute batch updates on a spreadsheet (add sheets, format cells, create charts, etc.)

### Values (Read)
- `sheets_get_values` - Read values from a single range in A1 notation (e.g., 'Sheet1!A1:B10')
- `sheets_batch_get_values` - Read values from multiple ranges at once

### Values (Write)
- `sheets_update_values` - Write values to a single range
- `sheets_batch_update_values` - Write values to multiple ranges at once
- `sheets_append_values` - Append values after the last row of data in a range
- `sheets_clear_values` - Clear values from a range while keeping formatting

---

## For MCP Users

Use this section if you want to **call** the google-sheets-mcp server from your own application via the Dedalus SDK.

### Prerequisites

1. A Dedalus API key (`dsk-live-*` or `dsk-test-*`)
2. The `dedalus-labs` Python SDK: `pip install dedalus-labs`

### Quick Start

See [`src/_client.py`](src/_client.py) for the complete working example.

### OAuth Flow

1. Your first request raises `AuthenticationError` with a `connect_url`
2. Open the URL in a browser to authorize Google Sheets access
3. After authorization, retry the request — credentials are now stored
4. Subsequent requests work without re-authorization

---

## For MCP Developers

Use this section if you want to **build, modify, or deploy** a Google Sheets MCP server like this one.

### Project Structure

```
src/
  main.py        # Entrypoint — loads .env and starts the server
  server.py      # MCPServer setup (port 8080, streamable HTTP)
  sheets.py      # All 10 Google Sheets tools + API connection
  _client.py     # Example client with OAuth browser flow
```

### Prerequisites

1. **Google Cloud project** with the [Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) enabled
2. **OAuth 2.0 credentials** — create a "Web application" client in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) and download the client secret JSON
3. **Dedalus API key** (`dsk-live-*` or `dsk-test-*`)
4. [uv](https://docs.astral.sh/uv/) package manager

### Environment Variables

Copy `.env.example` and fill in your values:

```bash
cp .env.example .env
```

**OAuth configuration** (from your Google client secret JSON):

```bash
OAUTH_ENABLED=true
OAUTH_AUTHORIZE_URL=https://accounts.google.com/o/oauth2/auth
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
OAUTH_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
OAUTH_CLIENT_SECRET=GOCSPX-<your-secret>
OAUTH_SCOPES_AVAILABLE=https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.readonly
OAUTH_BASE_URL=https://sheets.googleapis.com
```

**Dedalus platform**:

```bash
DEDALUS_API_KEY=dsk-live-...
DEDALUS_API_URL=https://api.dedaluslabs.ai
DEDALUS_AS_URL=https://as.dedaluslabs.ai
```

### Adding a New Tool

1. Define an async function in `sheets.py` with the `@tool` decorator
2. Add it to the `sheets_tools` list at the bottom of `sheets.py`

### Running Locally

```bash
cd google-sheets-mcp
uv sync
uv run python src/main.py
```

The server starts on **port 8080** and exposes `/mcp` via streamable HTTP.

## API Reference

- [Google Sheets API Overview](https://developers.google.com/sheets/api/guides/overview)
- [Google Sheets API Reference](https://developers.google.com/sheets/api/reference/rest)
