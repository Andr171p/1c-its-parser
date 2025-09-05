from typing import TypedDict

import asyncio
from datetime import datetime

from html2text import html2text
from playwright.async_api import Browser, Page, ElementHandle

from parser.utils import get_current_page

NEWS_URL = "https://its.1c.ru/news"

MONTHS: dict[str, str] = {
    "янв": "января",
    "фев": "февраля",
    "мар": "марта",
    "апр": "апреля",
    "май": "мая",
    "июн": "июня",
    "июл": "июля",
    "авг": "августа",
    "сен": "сентября",
    "окт": "октября",
    "ноя": "ноября",
    "дек": "декабря"
}


class NewsElement(TypedDict):
    title: str      # Заголовок новости
    url: str        # Адрес для перехода на полную новость
    date: str       # Дата публикации
    views: int      # Количество просмотров


def format_period_value(date: datetime) -> str:
    if date.month > 9:
        return f"{date.year}{date.month}"
    return f"{date.year}{date.month:02}"


async def set_period_value(page: Page, period_value: str) -> None:
    await page.evaluate(f"""() => {{
        const select = document.getElementById('news_filter_period');
        select.value = '{period_value}';
        const event = new Event('change', {{ bubbles: true }});
        select.dispatchEvent(event);
        }}""")
    await page.wait_for_load_state("networkidle")


async def extract_news_url(element: ElementHandle) -> str | None:
    link_element = await element.query_selector("a[href]")
    if not link_element:
        return None
    url = await link_element.get_attribute("href")
    if url is not None and not url.startswith("http"):
        return f"https://its.1c.ru{url}"
    return url


async def extract_news_title(element: ElementHandle) -> str:
    title_element = await element.query_selector(".link-item.news-item")
    if title_element is None:
        return "_"
    title = await title_element.text_content()
    return html2text(title.strip())


async def extract_news_date(element: ElementHandle) -> str:
    return await element.evaluate("""(element, MONTHS) => {
        const dateEl = element.querySelector('.journal-date');
        if (!dateEl) return '_';
        
        const day = dateEl.querySelector('.journal-date__day')?.textContent || '';
        const month = dateEl.querySelector('.journal-date__month')?.textContent || '';
        const year = dateEl.querySelector('.journal-date__year')?.textContent || '';
        
        return `${day} ${MONTHS[month] || month} 20${year.replace("'", "")}`;
    }""", MONTHS)


async def extract_news_views(element: ElementHandle) -> int:
    views_element = await element.query_selector(".logo.view")
    if views_element is None:
        return 0
    views = await views_element.text_content()
    return int(views.strip())


async def find_news(browser: Browser, date: datetime, sleep: int = 1) -> list[NewsElement]:
    page = await get_current_page(browser)
    await page.goto(NEWS_URL)
    await page.wait_for_selector("#news_filter")
    period_value = format_period_value(date)
    await set_period_value(page, period_value)
    await asyncio.sleep(sleep)
    news_items = await page.query_selector_all("#news_content .panel")
    news_elements: list[NewsElement] = []
    for news_item in news_items:
        url = await extract_news_url(news_item)
        if url is not None:
            title = await extract_news_title(news_item)
            date = await extract_news_date(news_item)
            views = await extract_news_views(news_item)
            news_elements.append(
                NewsElement(title=title, url=url, date=date, views=views)
            )
    return news_elements


async def parse_news(browser: Browser, url: str) -> dict[str, str]:
    page = await browser.new_page()

    await page.set_extra_http_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    })

    await page.goto(url, wait_until="networkidle", timeout=60000)

    return {
        "title": await page.text_content("#actinfo time"),
        "content": await page.text_content("#content p"),
        "date": await page.text_content(".header")
    }


async def execute_news_pipeline(browser: Browser) -> list[str]:
    elements = await find_news(browser, datetime(2025, 9, 1))
    for element in elements:
        text = await parse_news(browser, element["url"])
        print(text)
        print("\n\n")
    return ...
