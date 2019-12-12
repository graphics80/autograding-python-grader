"""
Test Runner for Python.
"""
from ast import NodeVisitor, ClassDef, FunctionDef, AsyncFunctionDef, parse
from pathlib import Path
from typing import Dict, overload

from .data import Hierarchy

# pylint: disable=invalid-name, no-self-use


class TestOrder(NodeVisitor):
    """
    Visits test_* methods in a file and caches their definition order.
    """

    _cache: Dict[Hierarchy, int] = {}

    def __init__(self, root: Hierarchy) -> None:
        super().__init__()
        self._hierarchy = [root]

    def visit_ClassDef(self, node: ClassDef) -> None:
        """
        Handles class definitions.
        """
        bases = {f"{b.value.id}.{b.attr}" for b in node.bases}
        if "unittest.TestCase" in bases:
            self._hierarchy.append(Hierarchy(node.name))
        self.generic_visit(node)
        self._hierarchy.pop()

    @overload
    def _visit_definition(self, node: FunctionDef) -> None:
        ...

    @overload
    def _visit_definition(self, node: AsyncFunctionDef) -> None:
        ...

    def _visit_definition(self, node):
        if node.name.startswith("test_"):
            self._cache[self.get_hierarchy(Hierarchy(node.name))] = node.lineno
        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        """
        Handles test definitions
        """
        self._visit_definition(node)

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> None:
        """
        Handles async test definitions
        """
        self._visit_definition(node)

    def get_hierarchy(self, name: Hierarchy) -> Hierarchy:
        """
        Returns the hierarchy :: joined.
        """
        return Hierarchy("::".join(self._hierarchy + [name]))

    @classmethod
    def lineno(cls, test_id: Hierarchy, source: Path) -> int:
        """
        Returns the line that the given test was defined on.
        """
        if test_id not in cls._cache:
            tree = parse(source.read_text(), source.name)
            cls(Hierarchy(test_id.split("::")[0])).visit(tree)
        return cls._cache[test_id]
