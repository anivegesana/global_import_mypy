from typing import List, Set, Tuple, Type, Union

from mypy.nodes import FuncItem, GlobalDecl, Import, ImportFrom, MypyFile
from mypy.options import Options
from mypy.plugin import Plugin
from mypy.traverser import TraverserVisitor
from typing_extensions import override


class GlobalImportVisitor(TraverserVisitor):
    @override
    def visit_mypy_file(self, o: MypyFile) -> None:
        self.current_file = o
        self.globals: List[List[str]] = [[]]
        self.imports: Set[Union[Import, ImportFrom]] = set()

        super().visit_mypy_file(o)

        o.imports.extend(self.imports)
        o.defs.extend(self.imports)
        del self.current_file, self.globals, self.imports

    @override
    def visit_func(self, o: FuncItem) -> None:
        self.globals.append([])
        super().visit_func(o)
        self.globals.pop()

    @override
    def visit_global_decl(self, o: GlobalDecl) -> None:
        self.globals[-1].extend(o.names)
        super().visit_global_decl(o)

    @override
    def visit_import(self, o: Import) -> None:
        for left, right in o.ids:
            if right is None:
                right = left
            if right in self.globals[-1]:
                self.imports.add(o)
        super().visit_import(o)

    @override
    def visit_import_from(self, o: ImportFrom) -> None:
        for left, right in o.names:
            if right is None:
                right = left
            if right in self.globals[-1]:
                self.imports.add(o)
        super().visit_import_from(o)


class GlobalImportMypyPlugin(Plugin):
    def __init__(self, options: Options):
        super().__init__(options)
        self.visitor = GlobalImportVisitor()

    def get_additional_deps(self, file: MypyFile) -> List[Tuple[int, str, int]]:
        file.accept(self.visitor)
        return []


def plugin(version: str) -> Type[GlobalImportMypyPlugin]:
    return GlobalImportMypyPlugin

