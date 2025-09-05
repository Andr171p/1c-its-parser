import asyncio

from playwright.async_api import async_playwright

from parser.auth import authenticate
from parser.settings import credentials
from parser.modules.db import parse_db
from parser.constants import DB_LINKS


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        await authenticate(browser, credentials=credentials)
        for db_link in DB_LINKS:
            docs = await parse_db(browser, db_link)
            print(len(docs))
            print(docs[-1])
        # await parse_page(browser, "https://its.1c.ru/db/edtdoc#content:10052:hdoc")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
