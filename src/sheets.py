# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Google Sheets API tools for google-sheets-mcp.

Read and manage Google Sheets via the Sheets REST API v4.
Ref: https://developers.google.com/sheets/api/guides/concepts
"""

import json
from typing import Any
from urllib.parse import quote

from mcp.types import TextContent, Tool

from dedalus_mcp.types import ToolAnnotations

from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys

# -----------------------------------------------------------------------------
# Connection
# -----------------------------------------------------------------------------

sheets = Connection(
    name="google-sheets-mcp",  # Must match server slug for OAuth callback
    secrets=SecretKeys(token="SHEETS_ACCESS_TOKEN"),
    base_url="https://sheets.googleapis.com",
    auth_header_format="Bearer {api_key}",
)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

SheetsResult = list[TextContent]


async def _req(method: HttpMethod, path: str, body: dict | None = None) -> SheetsResult:
    """Make a Sheets API request and return JSON as TextContent."""
    ctx = get_context()
    resp = await ctx.dispatch("google-sheets-mcp", HttpRequest(method=method, path=path, body=body))
    if resp.success:
        data = resp.response.body or {}
        return [TextContent(type="text", text=json.dumps(data, indent=2))]
    error = resp.error.message if resp.error else "Request failed"
    return [TextContent(type="text", text=json.dumps({"error": error}, indent=2))]


def _encode_range(range_a1: str) -> str:
    """URL-encode an A1 notation range, preserving safe characters."""
    return quote(range_a1, safe="!:$'(),-._~")


# -----------------------------------------------------------------------------
# Spreadsheet Tools
# -----------------------------------------------------------------------------


@tool(
    description="Get spreadsheet metadata including title, locale, sheets, and named ranges.",
    tags=["spreadsheet", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def sheets_get_spreadsheet(
    spreadsheet_id: str,
    include_grid_data: bool = False,
    ranges: str = "",
    fields: str = "",
) -> SheetsResult:
    """Get spreadsheet metadata. Optionally include grid data for specific ranges."""
    params = [f"includeGridData={str(include_grid_data).lower()}"]
    if ranges:
        for r in ranges.split(","):
            params.append(f"ranges={r.strip()}")
    if fields:
        params.append(f"fields={fields}")

    query_string = "&".join(params)
    return await _req(HttpMethod.GET, f"/v4/spreadsheets/{spreadsheet_id}?{query_string}")


@tool(
    description="List all sheets/tabs in a spreadsheet with their properties (ID, title, index, grid size).",
    tags=["spreadsheet", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def sheets_list_sheets(spreadsheet_id: str) -> SheetsResult:
    """List sheets/tabs with compact metadata."""
    fields = "spreadsheetId,properties(title),sheets(properties(sheetId,title,index,gridProperties))"
    return await _req(
        HttpMethod.GET,
        f"/v4/spreadsheets/{spreadsheet_id}?fields={fields}",
    )


# -----------------------------------------------------------------------------
# Values Tools (Read)
# -----------------------------------------------------------------------------


@tool(
    description="Read values from a single range in A1 notation (e.g., 'Sheet1!A1:B10').",
    tags=["values", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def sheets_get_values(
    spreadsheet_id: str,
    range: str,
    major_dimension: str = "ROWS",
    value_render_option: str = "FORMATTED_VALUE",
    date_time_render_option: str = "SERIAL_NUMBER",
) -> SheetsResult:
    """Get values from a range. Returns 2D array of cell values."""
    encoded_range = _encode_range(range)
    params = [
        f"majorDimension={major_dimension}",
        f"valueRenderOption={value_render_option}",
        f"dateTimeRenderOption={date_time_render_option}",
    ]
    query_string = "&".join(params)
    return await _req(
        HttpMethod.GET,
        f"/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}?{query_string}",
    )


@tool(
    description="Read values from multiple ranges at once. More efficient than multiple single-range calls.",
    tags=["values", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def sheets_batch_get_values(
    spreadsheet_id: str,
    ranges: str,
    major_dimension: str = "ROWS",
    value_render_option: str = "FORMATTED_VALUE",
    date_time_render_option: str = "SERIAL_NUMBER",
) -> SheetsResult:
    """Get values from multiple ranges. Ranges should be comma-separated A1 notation."""
    params = [
        f"majorDimension={major_dimension}",
        f"valueRenderOption={value_render_option}",
        f"dateTimeRenderOption={date_time_render_option}",
    ]
    for r in ranges.split(","):
        params.append(f"ranges={r.strip()}")

    query_string = "&".join(params)
    return await _req(
        HttpMethod.GET,
        f"/v4/spreadsheets/{spreadsheet_id}/values:batchGet?{query_string}",
    )


# -----------------------------------------------------------------------------
# Values Tools (Write)
# -----------------------------------------------------------------------------


@tool(
    description="Write values to a single range. Values are parsed as if typed by user (USER_ENTERED).",
    tags=["values", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def sheets_update_values(
    spreadsheet_id: str,
    range: str,
    values: list[list[Any]],
    value_input_option: str = "USER_ENTERED",
    include_values_in_response: bool = False,
) -> SheetsResult:
    """Update values in a range. Values is a 2D array matching the range dimensions."""
    encoded_range = _encode_range(range)
    params = [
        f"valueInputOption={value_input_option}",
        f"includeValuesInResponse={str(include_values_in_response).lower()}",
    ]
    query_string = "&".join(params)
    body = {"values": values}
    return await _req(
        HttpMethod.PUT,
        f"/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}?{query_string}",
        body,
    )


@tool(
    description="Write values to multiple ranges at once. More efficient than multiple single-range updates.",
    tags=["values", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def sheets_batch_update_values(
    spreadsheet_id: str,
    data: list[dict[str, Any]],
    value_input_option: str = "USER_ENTERED",
    include_values_in_response: bool = False,
) -> SheetsResult:
    """Batch update values. Data is list of {range: str, values: list[list]} objects."""
    body = {
        "valueInputOption": value_input_option,
        "includeValuesInResponse": include_values_in_response,
        "data": data,
    }
    return await _req(
        HttpMethod.POST,
        f"/v4/spreadsheets/{spreadsheet_id}/values:batchUpdate",
        body,
    )


@tool(
    description="Append values after the last row of data in a range. Useful for adding new rows.",
    tags=["values", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def sheets_append_values(
    spreadsheet_id: str,
    range: str,
    values: list[list[Any]],
    value_input_option: str = "USER_ENTERED",
    insert_data_option: str = "INSERT_ROWS",
    include_values_in_response: bool = False,
) -> SheetsResult:
    """Append values after existing data. INSERT_ROWS adds new rows, OVERWRITE overwrites."""
    encoded_range = _encode_range(range)
    params = [
        f"valueInputOption={value_input_option}",
        f"insertDataOption={insert_data_option}",
        f"includeValuesInResponse={str(include_values_in_response).lower()}",
    ]
    query_string = "&".join(params)
    body = {"values": values}
    return await _req(
        HttpMethod.POST,
        f"/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}:append?{query_string}",
        body,
    )


@tool(
    description="Clear values from a range while keeping formatting.",
    tags=["values", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def sheets_clear_values(
    spreadsheet_id: str,
    range: str,
) -> SheetsResult:
    """Clear values from a range. Formatting is preserved."""
    encoded_range = _encode_range(range)
    return await _req(
        HttpMethod.POST,
        f"/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}:clear",
        {},
    )


# -----------------------------------------------------------------------------
# Spreadsheet Mutation Tools
# -----------------------------------------------------------------------------


@tool(
    description="Execute batch updates on a spreadsheet (add sheets, format cells, create charts, etc.).",
    tags=["spreadsheet", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def sheets_batch_update(
    spreadsheet_id: str,
    requests: list[dict[str, Any]],
    include_spreadsheet_in_response: bool = False,
) -> SheetsResult:
    """Execute batch spreadsheet updates. Requests is list of update request objects."""
    body = {
        "requests": requests,
        "includeSpreadsheetInResponse": include_spreadsheet_in_response,
    }
    return await _req(
        HttpMethod.POST,
        f"/v4/spreadsheets/{spreadsheet_id}:batchUpdate",
        body,
    )


@tool(
    description="Create a new spreadsheet with optional title and sheets.",
    tags=["spreadsheet", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def sheets_create(
    title: str,
    sheet_titles: str = "",
) -> SheetsResult:
    """Create a new spreadsheet. Optionally provide comma-separated sheet titles."""
    body: dict[str, Any] = {
        "properties": {"title": title},
    }
    if sheet_titles:
        body["sheets"] = [{"properties": {"title": t.strip()}} for t in sheet_titles.split(",")]

    return await _req(
        HttpMethod.POST,
        "/v4/spreadsheets",
        body,
    )


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------

sheets_tools: list[Tool] = [
    # Spreadsheet
    sheets_get_spreadsheet,
    sheets_list_sheets,
    sheets_create,
    sheets_batch_update,
    # Values (Read)
    sheets_get_values,
    sheets_batch_get_values,
    # Values (Write)
    sheets_update_values,
    sheets_batch_update_values,
    sheets_append_values,
    sheets_clear_values,
]
