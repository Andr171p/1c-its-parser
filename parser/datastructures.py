from __future__ import annotations

from typing import Literal

from collections import deque
from collections.abc import Iterator

from pydantic import BaseModel, Field


class ChapterNode(BaseModel):
    """Дерево для работы с параграфами в разделе документации"""
    name: str
    url: str
    children: list[ChapterNode] = Field(default_factory=list)
    parent: ChapterNode | None = None

    @property
    def type(self) -> Literal["root", "children", "leaf"]:
        """Тип узла дерева"""
        if self.parent is None:
            return "root"
        elif not self.children:
            return "leaf"
        return "children"

    def path(self) -> str:
        """Полный путь до выбранного узла в формате: 'name1|name2|...'"""
        parts: list[str] = []
        current = self
        while current is not None:
            parts.append(current.name)
            current = current.parent
        return "|".join(parts[::-1])

    def max_depth(self) -> int:
        """Максимальная глубина относительно выбранного узла"""
        if not self.children:
            return 0
        max_depth = 0
        for child in self.children:
            depth = child.max_depth()
            if depth > max_depth:
                max_depth = depth
        return max_depth + 1

    def current_depth(self) -> int:
        """Текущая глубина"""
        depth = 0
        current = self.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth

    def add_child(self, child: ChapterNode) -> None:
        """Добавляет наследника"""
        child.parent = self
        self.children.append(child)

    def find(self, url: str) -> ChapterNode | None:
        """Находит узел по его URL адресу"""
        if self.url == url:
            return self
        for child in self.children:
            paragraph = child.find(url)
            if paragraph is not None:
                return paragraph
        return None

    def __repr__(self) -> str:
        return self.to_str(indent=0)

    def to_str(self, indent: int = 0) -> str:
        """Приводит вершину к строковому формату (для отладки и логирования)"""
        indent_str = "---" * indent
        node_str = f"{indent_str}{self.name} ({self.url}) [{self.type}]\n"
        for child in self.children:
            node_str += child.to_str(indent + 1)
        return node_str

    def iterate_dfs(self) -> Iterator[ChapterNode]:
        """Итерация в глубину (Depth-First Search)"""
        yield self
        for child in self.children:
            yield from child.iterate_dfs()

    def iterate_bfs(self) -> Iterator[ChapterNode]:
        """Итерация в ширину (Breadth-First Search"""
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            queue.extend(node.children)

    def iterate_leaves(self) -> Iterator[ChapterNode]:
        """Итерация только узлам являющимися листьями"""
        for node in self.iterate_dfs():
            if node.type == "leaf":
                yield node
