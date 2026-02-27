# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Google Sheets API tools for google-sheets-mcp.

Read and manage Google Sheets via the Sheets REST API v4.
Ref: https://developers.google.com/sheets/api/guides/concepts
"""

from typing import Any
from urllib.parse import urlencode

from pydantic import BaseModel

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


class SheetsResult(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


async def _request(
    method: HttpMethod,
    path: str,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> SheetsResult:
    """Make a Sheets API request and return result."""
    ctx = get_context()

    if params:
        query_string = urlencode({k: v for k, v in params.items() if v is not None})
        if query_string:
            path = f"{path}?{query_string}"

    request = HttpRequest(method=method, path=path, body=body)
    response = await ctx.dispatch("google-sheets-mcp", request)

    if response.success:
        return SheetsResult(success=True, data=response.response.body)

    msg = response.error.message if response.error else "Request failed"
    return SheetsResult(success=False, error=msg)


# -----------------------------------------------------------------------------
# Spreadsheet Tools
# -----------------------------------------------------------------------------


@tool(description="Get spreadsheet metadata including title, locale, sheets, and named ranges")
async def sheets_get_spreadsheet(
    spreadsheet_id: str,
    include_grid_data: bool = False,
    ranges: str | None = None,
    fields: str | None = None,
) -> SheetsResult:
    params: dict[str, Any] = {
        "includeGridData": str(include_grid_data).lower(),
    }
    if ranges:
        params["ranges"] = ranges
    if fields:
        params["fields"] = fields

    return await _request(
        HttpMethod.GET,
        f"/v4/spreadsheets/{spreadsheet_id}",
        params=params,
    )


@tool(description="List all sheets/tabs in a spreadsheet with their properties (ID, title, index, grid size)")
async def sheets_list_sheets(spreadsheet_id: str) -> SheetsResult:
    fields = "spreadsheetId,properties(title),sheets(properties(sheetId,title,index,gridProperties))"
    return await _request(
        HttpMethod.GET,
        f"/v4/spreadsheets/{spreadsheet_id}",
        params={"fields": fields},
    )


# -----------------------------------------------------------------------------
# Values Tools (Read)
# -----------------------------------------------------------------------------


@tool(description="Read values from a single range in A1 notation (e.g., 'Sheet1!A1:B10')")
async def sheets_get_values(
    spreadsheet_id: str,
    range: str,
    major_dimension: str = "ROWS",
    value_render_option: str = "FORMATTED_VALUE",
    date_time_render_option: str = "SERIAL_NUMBER",
) -> SheetsResult:
    return await _request(
        HttpMethod.GET,
        f"/v4/spreadsheets/{spreadsheet_id}/values/{range}",
        params={
            "majorDimension": major_dimension,
            "valueRenderOption": value_render_option,
            "dateTimeRenderOption": date_time_render_option,
        },
    )


@tool(description="Read values from multiple ranges at once. More efficient than multiple single-range calls")
async def sheets_batch_get_values(
    spreadsheet_id: str,
    ranges: str,
    major_dimension: str = "ROWS",
    value_render_option: str = "FORMATTED_VALUE",
    date_time_render_option: str = "SERIAL_NUMBER",
) -> SheetsResult:
    return await _request(
        HttpMethod.GET,
        f"/v4/spreadsheets/{spreadsheet_id}/values:batchGet",
        params={
            "ranges": ranges,
            "majorDimension": major_dimension,
            "valueRenderOption": value_render_option,
            "dateTimeRenderOption": date_time_render_option,
        },
    )


# -----------------------------------------------------------------------------
# Values Tools (Write)
# -----------------------------------------------------------------------------


@tool(description="Write values to a single range. Values are parsed as if typed by user (USER_ENTERED)")
async def sheets_update_values(
    spreadsheet_id: str,
    range: str,
    values: list[list[Any]],
    value_input_option: str = "USER_ENTERED",
    include_values_in_response: bool = False,
) -> SheetsResult:
    return await _request(
        HttpMethod.PUT,
        f"/v4/spreadsheets/{spreadsheet_id}/values/{range}",
        params={
            "valueInputOption": value_input_option,
            "includeValuesInResponse": str(include_values_in_response).lower(),
        },
        body={"values": values},
    )


@tool(description="Write values to multiple ranges at once. More efficient than multiple single-range updates")
async def sheets_batch_update_values(
    spreadsheet_id: str,
    data: list[dict[str, Any]],
    value_input_option: str = "USER_ENTERED",
    include_values_in_response: bool = False,
) -> SheetsResult:
    return await _request(
        HttpMethod.POST,
        f"/v4/spreadsheets/{spreadsheet_id}/values:batchUpdate",
        body={
            "valueInputOption": value_input_option,
            "includeValuesInResponse": include_values_in_response,
            "data": data,
        },
    )


@tool(description="Append values after the last row of data in a range. Useful for adding new rows")
async def sheets_append_values(
    spreadsheet_id: str,
    range: str,
    values: list[list[Any]],
    value_input_option: str = "USER_ENTERED",
    insert_data_option: str = "INSERT_ROWS",
    include_values_in_response: bool = False,
) -> SheetsResult:
    return await _request(
        HttpMethod.POST,
        f"/v4/spreadsheets/{spreadsheet_id}/values/{range}:append",
        params={
            "valueInputOption": value_input_option,
            "insertDataOption": insert_data_option,
            "includeValuesInResponse": str(include_values_in_response).lower(),
        },
        body={"values": values},
    )


@tool(description="Clear values from a range while keeping formatting")
async def sheets_clear_values(
    spreadsheet_id: str,
    range: str,
) -> SheetsResult:
    return await _request(
        HttpMethod.POST,
        f"/v4/spreadsheets/{spreadsheet_id}/values/{range}:clear",
    )


# -----------------------------------------------------------------------------
# Spreadsheet Mutation Tools
# -----------------------------------------------------------------------------


@tool(description="Execute batch updates on a spreadsheet (add sheets, format cells, create charts, etc.)")
async def sheets_batch_update(
    spreadsheet_id: str,
    requests: list[dict[str, Any]],
    include_spreadsheet_in_response: bool = False,
) -> SheetsResult:
    return await _request(
        HttpMethod.POST,
        f"/v4/spreadsheets/{spreadsheet_id}:batchUpdate",
        body={
            "requests": requests,
            "includeSpreadsheetInResponse": include_spreadsheet_in_response,
        },
    )


@tool(description="Create a new spreadsheet with optional title and sheets")
async def sheets_create(
    spreadsheet_title: str,
    sheet_titles: str | None = None,
) -> SheetsResult:
    body: dict[str, Any] = {
        "properties": {"title": spreadsheet_title},
    }
    if sheet_titles:
        body["sheets"] = [{"properties": {"title": t.strip()}} for t in sheet_titles.split(",")]

    return await _request(
        HttpMethod.POST,
        "/v4/spreadsheets",
        body=body,
    )


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------

sheets_tools = [
    sheets_get_spreadsheet,
    sheets_list_sheets,
    sheets_create,
    sheets_batch_update,
    sheets_get_values,
    sheets_batch_get_values,
    sheets_update_values,
    sheets_batch_update_values,
    sheets_append_values,
    sheets_clear_values,
]
