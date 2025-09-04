import logging
import re
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page

logger = logging.getLogger(__name__)


async def get_current_page(browser: Browser) -> Page:
    """Получает текущую страницу в браузере"""
    if not browser.contexts:
        context = await browser.new_context()
        return await context.new_page()
    context = browser.contexts[0]
    if not context.pages:
        return await context.new_page()
    return context.pages[-1]


def remove_inner_hrefs(html_content: str, base_url: str) -> str:
    """Удаляет все доменные ссылки на странице"""
    soup = BeautifulSoup(html_content, "html.parser")
    current_domain = urlparse(base_url).netloc
    for a in soup.find_all("a", href=True):
        href = a["href"]
        try:
            if not href.startswith(("http://", "https://")):
                url = urljoin(base_url, href)
            else:
                url = href
            link_domain = urlparse(url).netloc
            if link_domain == current_domain or link_domain.endswith("." + current_domain):
                a.decompose()
        except Exception as e:
            logger.exception("Error while href removing: %s", str(e))
            continue
    return str(soup)


def remove_md_links(md_text: str, base_url: str) -> str:
    """Удаляет все относительные ссылки в Markdown тексте"""
    domain_pattern = re.escape(base_url)
    patterns: list[str] = [
        # Изображения
        r"!\[.*?\]\(.*?" + domain_pattern + r".*?\)",
        r"!\[\]\(.*?" + domain_pattern + r".*?\)",
        # Ссылки
        r"\[.*?\]\(.*?" + domain_pattern + r".*?\)",
        # Простые URL
        r"https?://[^\s]*" + domain_pattern + r"[^\s]*",
        # Относительные ссылки
        r"!\[.*?\]\(/.*?\)",
        r"!\[\]\(/.*?\)",
        r"\[.*?\]\(/.*?\)"
    ]
    for pattern in patterns:
        md_text = re.sub(pattern, "", md_text)
    return md_text
