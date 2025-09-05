from playwright.async_api import Browser, ElementHandle

from constants import URL
from schemas import ParagraphNode
from utils import get_current_page, html2md_pipeline


async def parse_paragraphs_tree(browser: Browser, root_path: str) -> ParagraphNode:
    """Получает дерево навигации по параграфам в документации"""
    url = f"{URL}{root_path}"
    root_node = ParagraphNode(name="Root", url=url)
    page = await get_current_page(browser)
    await page.goto(url)
    div_element = await page.wait_for_selector("#w_metadata_toc")
    ul_element = await div_element.query_selector("ul")
    li_element = await ul_element.query_selector("li")
    await find_nested_paragraphs(li_element, root_node)
    return root_node


async def find_nested_paragraphs(
        li_element: ElementHandle,
        node: ParagraphNode,
        current_depth: int = 0,
        max_depth: int = 5
) -> None:
    """Находит вложенные параграфы"""
    if current_depth > max_depth:
        return
    link_element = await li_element.query_selector("a")
    child_node = ParagraphNode(
        name=await link_element.text_content(),
        url=f"{URL}{await link_element.get_attribute("href")}",
    )
    node.add_child(child_node)
    ul_element = await li_element.query_selector("ul")
    if not ul_element:
        return
    li_elements = await ul_element.query_selector_all("li")
    for li_element in li_elements:
        await find_nested_paragraphs(li_element, child_node, current_depth + 1, max_depth)


async def parse_document(browser: Browser, url: str) -> str:
    """Парсит текстовый контент документа в формате Markdown"""
    page = await get_current_page(browser)
    await page.goto(url)
    await page.wait_for_selector("#w_metadata_doc_frame")
    frame_content = page.frame_locator("#w_metadata_doc_frame")
    await frame_content.locator("body").wait_for()
    html_content = await frame_content.locator("body").inner_html()
    return html2md_pipeline(html_content, URL)


async def parse_doc_chapter(browser: Browser, chapter_path: str) -> list[str]:
    documents: list[str] = []
    paragraphs_tree = await parse_paragraphs_tree(browser, chapter_path)
    for paragraph in paragraphs_tree.iterate_leaves():
        text = await parse_document(browser, paragraph.url)
        documents.append(f"{paragraph.path()}\n\n{text}")
    return documents
