# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client demonstrating OAuth browser flow for Google Sheets.

Environment variables:
    DEDALUS_API_KEY: Your Dedalus API key (dsk_*)
"""

import asyncio
import webbrowser

from dotenv import load_dotenv

load_dotenv()

from dedalus_labs import AsyncDedalus, AuthenticationError, DedalusRunner
from dedalus_labs.utils.stream import stream_async


async def main():
    client = AsyncDedalus()
    runner = DedalusRunner(client)

    async def run():
        return runner.run(
            input="List my spreadsheets and show me the first one",
            model="openai/gpt-5.2",
            mcp_servers=["anny_personal/google-sheets-mcp"],
            stream=True,
        )

    try:
        stream = await run()
        await stream_async(stream)
    except AuthenticationError as err:
        body = err.body if isinstance(err.body, dict) else {}
        url = body.get("connect_url") or body.get("detail", {}).get("connect_url")
        if not url:
            raise
        print(f"\nOAuth required. Open: {url}")
        webbrowser.open(url)
        input("Press Enter after completing OAuth...")
        stream = await run()
        await stream_async(stream)


if __name__ == "__main__":
    asyncio.run(main())
