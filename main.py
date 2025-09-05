import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Page

from parser.modules.db import parse_db
from parser.constants import DB_LINKS

load_dotenv()

LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")

URL = "https://login.1c.ru/login"


async def get_current_page(browser: Browser) -> Page:
    if not browser.contexts:
        context = await browser.new_context()
        return await context.new_page()
    context = browser.contexts[0]
    if not context.pages:
        return await context.new_page()
    return context.pages[-1]


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await get_current_page(browser)
        await page.goto(URL)
        await page.fill("#username", LOGIN)
        await page.fill("#password", PASSWORD)
        await page.click("#loginButton")
        await page.wait_for_load_state("networkidle")
        if page.url != "https://its.1c.ru/login":
            print("Успешный вход!")
        else:
            print("Ошибка входа")
        for db_link in DB_LINKS:
            docs = await parse_db(browser, db_link)
            print(len(docs))
            print(docs[-1])
        # await parse_page(browser, "https://its.1c.ru/db/edtdoc#content:10052:hdoc")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
