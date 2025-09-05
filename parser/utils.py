import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify
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


def html2md_pipeline(html_content: str, base_url: str) -> str:
    return md_links_filter(
        markdownify(
            html_links_filter(
                preserve_image_links(html_content, base_url), base_url
            )
        ), base_url
    )


def preserve_image_links(html_content: str, base_url: str) -> str:
    """
    Сохраняет абсолютные URL картинок на странице, преобразуя относительные пути в абсолютные
    """
    soup = BeautifulSoup(html_content, "html.parser")
    for img in soup.find_all("img", src=True):
        src = img["src"]
        try:
            if not src.startswith(("http://", "https://", "data:")):
                url = urljoin(base_url, src)
                img["src"] = url
            elif src.startswith(("http://", "https://")):
                img["src"] = src
        except Exception as e:
            logger.exception("Error while preserving image URL: %s", str(e))
            continue
    return str(soup)


def html_links_filter(html_content: str, base_url: str) -> str:
    """Удаляет все доменные ссылки на странице"""
    soup = BeautifulSoup(html_content, "html.parser")
    current_domain = urlparse(base_url).netloc
    for a in soup.find_all("a", href=True):
        href = a["href"]
        try:
            if "image" in href:
                continue
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


def md_links_filter(md_text: str, base_url: str) -> str:
    """Удаляет все относительные ссылки в Markdown тексте, но сохраняет изображения"""
    # Временная замена изображений перед обработкой
    image_placeholders = {}
    # Находим и временно заменяем все изображения

    def replace_images(match):
        placeholder = f"@@IMAGE_{len(image_placeholders)}@@"
        image_placeholders[placeholder] = match.group(0)
        return placeholder
    # Паттерн для изображений Markdown
    image_pattern = r"!\[.*?\]\([^)]*\)"
    md_text = re.sub(image_pattern, replace_images, md_text)
    # Теперь удаляем все ссылки
    domain = urlparse(base_url).netloc
    domain_pattern = re.escape(domain)
    base_url_pattern = re.escape(base_url)
    patterns = [
        # Markdown ссылки
        r"\[(.*?)\]\([^)]*" + domain_pattern + r"[^)]*\)",
        r"\[(.*?)\]\([^)]*" + base_url_pattern + r"[^)]*\)",
        r"\[(.*?)\]\(/[^)]*\)",
        # Простые URL
        r"https?://[^\s]*" + domain_pattern + r"[^\s]*",
        r"https?://[^\s]*" + base_url_pattern + r"[^\s]*",
        r"/[^\s/\?]*"
    ]
    for pattern in patterns:
        if pattern.startswith(r"\["):
            md_text = re.sub(pattern, r"\1", md_text)
        else:
            md_text = re.sub(pattern, "", md_text)
    for placeholder, image in image_placeholders.items():
        md_text = md_text.replace(placeholder, image)
    return md_text
