from playwright.async_api import Browser, ElementHandle

from ..constants import URL
from ..datastructures import ChapterNode
from ..utils import get_current_page, html2md_pipeline


async def extract_chapter_tree(browser: Browser, root_path: str) -> ChapterNode:
    """Получает дерево навигации по главам в документации

    :param browser: Объект браузера.
    :param root_path: Основной путь до нужного раздела с документацией.
    :return Дерево с вложенными в него главами и разделами.
    """
    url = f"{URL}{root_path}"
    root_node = ChapterNode(name="Root", url=url)
    page = await get_current_page(browser)
    await page.goto(url)
    div_element = await page.wait_for_selector("#w_metadata_toc")
    ul_element = await div_element.query_selector("ul")
    li_element = await ul_element.query_selector("li")
    await extract_nested_chapters(li_element, root_node)
    return root_node


async def extract_nested_chapters(
        li_element: ElementHandle,
        node: ChapterNode,
        current_depth: int = 0,
        max_depth: int = 5
) -> None:
    """Рекурсивно находит вложенные главы.

    :param li_element: Элемент содержащий главу.
    :param node: Текущий узел дерева (текущая глава).
    :param current_depth: Текущая глубина рекурсии.
    :param max_depth: Максимальная глубина рекурсии.
    """
    if current_depth > max_depth:
        return
    link_element = await li_element.query_selector("a")
    child_node = ChapterNode(
        name=await link_element.text_content(),
        url=f"{URL}{await link_element.get_attribute("href")}",
    )
    node.add_child(child_node)
    ul_element = await li_element.query_selector("ul")
    if not ul_element:
        return
    li_elements = await ul_element.query_selector_all("li")
    for li_element in li_elements:
        await extract_nested_chapters(li_element, child_node, current_depth + 1, max_depth)


async def parse_document_content(browser: Browser, url: str) -> str:
    """Парсит текстовый контент документа в формате Markdown

    :param browser: Текущий объект браузера.
    :param url: URL адрес страницы с документом.
    :return Содержимое документа в формате Markdown.
    """
    page = await get_current_page(browser)
    await page.goto(url)
    await page.wait_for_selector("#w_metadata_doc_frame")
    frame_content = page.frame_locator("#w_metadata_doc_frame")
    await frame_content.locator("body").wait_for()
    html_content = await frame_content.locator("body").inner_html()
    return html2md_pipeline(html_content, URL)


async def parse_db(browser: Browser, db_path: str) -> list[str]:
    """Выполняет парсинг заданного раздела документации.

    :param browser: Текущий объект браузера.
    :param db_path: Ссылка на документацию.
    :return: Массив из полученных страниц в формате Markdown.
    """
    documents: list[str] = []
    chapter_tree = await extract_chapter_tree(browser, db_path)
    for chapter in chapter_tree.iterate_leaves():
        document_content = await parse_document_content(browser, chapter.url)
        documents.append(f"{chapter.path()}\n\n{document_content}")
    return documents
