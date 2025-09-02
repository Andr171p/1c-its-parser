from __future__ import annotations

import asyncio

from playwright.async_api import Browser, Page, ElementHandle
from pydantic import BaseModel, Field

from utils import get_current_page

URL = "https://its.1c.ru"


class ParagraphNode(BaseModel):
    name: str
    url: str
    child: list[ParagraphNode] = Field(default_factory=list)
    parent: ParagraphNode | None = None

    def path(self) -> str:
        nodes = [self]
        current = self.parent
        while current is not None:
            nodes.append(current.name)
            current = current.parent
        return "|".join(nodes[::-1])

    def add_child(self, child: ParagraphNode) -> None:
        child.parent = self
        self.child.append(child)

    def find(self, url: str) -> ParagraphNode | None:
        if self.url == url:
            return self
        for child in self.child:
            paragraph = child.find(url)
            if paragraph is None:
                return None
            return paragraph


async def find_paragraphs_urls(browser: Browser) -> set[str]:
    links: set[str] = set()
    root_node = ParagraphNode(name="Root", url=f"{URL}/db/edtdoc")
    page = await get_current_page(browser)
    await page.goto(f"{URL}/db/edtdoc")
    div_element = await page.wait_for_selector("#w_metadata_toc")
    ul_element = await div_element.query_selector("ul")
    li_element = await ul_element.query_selector("li")
    await find_nested_paragraphs(li_element, root_node)
    # node = root_node.find("https://its.1c.ru/db/edtdoc/content/5/hdoc")
    print(root_node)
    await asyncio.sleep(10)
    return links


async def find_nested_paragraphs(
        li_element: ElementHandle, node: ParagraphNode, max_depth: int = 2
) -> None:
    depth = 0
    if depth > max_depth:
        return
    link_element = await li_element.query_selector("a")
    # print(await link_element.text_content())
    # print(await link_element.get_attribute("href"))
    # links.add(f"{URL}{await link_element.get_attribute("href")}")
    node.add_child(ParagraphNode(
        name=await link_element.text_content(),
        url=f"{URL}{await link_element.get_attribute("href")}",
    ))
    ul_element = await li_element.query_selector("ul")
    if not ul_element:
        # print("Ветвь получена")
        return
    li_elements = await ul_element.query_selector_all("li")
    for li_element in li_elements:
        depth += 1
        await find_nested_paragraphs(li_element, node)
