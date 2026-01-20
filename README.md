# `google-sheets-mcp`

Dedalus MCP server for **Google Sheets API v4** (read + write).

## Quickstart

```bash
cd /Users/annyzhou/Desktop/google-sheets-mcp
uv sync
```

## Google OAuth (required)

Quick link: enable/verify APIs in Google Cloud Console: `https://console.cloud.google.com/apis/`

1) In Google Cloud Console:
- Enable **Google Sheets API**
- (Optional) Enable **Google Drive API** (needed for Drive search tools)
- Create **OAuth client ID** → **Desktop app**

If you skip enabling Sheets API, Google will return **HTTP 403** “API disabled / not used in project”.

2) Point the repo at your OAuth client JSON:

```bash
export GOOGLE_OAUTH_CREDENTIALS="/absolute/path/to/oauth-client.json"
```

3) Run the one-time auth flow (opens a browser, stores tokens locally):

```bash
uv run python -c 'from src.gsheets_oauth import ensure_gsheets_access_token; ensure_gsheets_access_token(interactive=True)'
```

Tokens are stored at `~/.config/google-sheets-mcp/tokens.json` by default (override with `GSHEETS_TOKEN_PATH`).

If you previously authenticated with read-only scopes, you must re-run the auth command after upgrading to write tools.

## Run the MCP server

```bash
export DEDALUS_AS_URL="https://as.dedaluslabs.ai"   # optional
export DEDALUS_API_KEY="..."                        # required when auth is enabled
uv run python -m src.main
```

## Tools

Tools are defined in `src/gsheets.py` (see `gsheets_tools` list).
