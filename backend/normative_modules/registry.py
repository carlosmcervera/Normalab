from typing import Dict, List, Optional

from normative_modules.base import NormativeModule


class ModuleRegistry:
    def __init__(self):
        self._modules: Dict[str, NormativeModule] = {}

    def register(self, module: NormativeModule):
        if not module.code:
            raise ValueError("El módulo debe tener un código")
        self._modules[module.code] = module

    def get(self, code: str) -> Optional[NormativeModule]:
        return self._modules.get(code)

    def all(self) -> List[NormativeModule]:
        return list(self._modules.values())

    def metas(self) -> List[dict]:
        return [m.meta() for m in self._modules.values()]


registry = ModuleRegistry()


def bootstrap_modules():
    """Import and register all normative modules. Adding a new normative only
    requires creating its module class and registering it here."""
    from normative_modules.rsciei.module import RscieiModule
    from normative_modules.placeholders import (
        CteModule,
        RebtModule,
        RiteModule,
        AccesibilidadModule,
    )

    registry.register(RscieiModule())
    registry.register(CteModule())
    registry.register(RebtModule())
    registry.register(RiteModule())
    registry.register(AccesibilidadModule())
    return registry
