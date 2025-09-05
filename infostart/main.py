import asyncio

from playwright.async_api import async_playwright
from html_to_markdown import convert_to_markdown

from infostart.constants import URL
from parser.utils import get_current_page


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await get_current_page(browser)
        await page.goto(f"{URL}/1c/")
        await page.wait_for_selector(".publication-item")
        elements = await page.query_selector_all(".publication-name a.font-md")
        links: list[str] = []
        for element in elements:
            item_text = await element.text_content()
            item_link = await element.get_attribute("href")
            print(f"{item_text}:{URL + item_link}")
            links.append(URL + item_link)
        for link in links:
            print(link)
            await page.goto(link, wait_until="networkidle")
            await page.wait_for_selector('.center-side-wrap', timeout=10000)
            element_html = await page.evaluate('''() => {
                        const element = document.querySelector('.center-side-wrap');
                        return element ? element.outerHTML : null;
                    }''')
            ...
            text = convert_to_markdown(element_html)
            print(text)
            break
        await browser.close()


asyncio.run(main())
