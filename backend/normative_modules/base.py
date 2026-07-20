from typing import Optional


class NormativeModule:
    """Base class for a decoupled normative module.

    Each normative (RSCIEI, CTE, REBT, ...) is implemented as a subclass and
    registered in the ModuleRegistry. A module encapsulates its own schema
    (wizard), rules engine (compute) and report template (build_report).
    """

    code: str = ""
    name: str = ""
    short_name: str = ""
    description: str = ""
    category: str = ""
    status: str = "placeholder"  # "operativo" | "placeholder"
    version: str = "1.0.0"
    legal_reference: str = ""
    icon: str = "file-text"
    accent: str = "slate"

    def meta(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "short_name": self.short_name or self.code,
            "description": self.description,
            "category": self.category,
            "status": self.status,
            "version": self.version,
            "legal_reference": self.legal_reference,
            "icon": self.icon,
            "accent": self.accent,
        }

    def get_schema(self) -> Optional[dict]:
        """Return the wizard schema (steps + fields) for dynamic rendering."""
        return None

    def compute(self, data: dict) -> dict:
        """Run validations, calculations and produce results + observations."""
        raise NotImplementedError("Este módulo aún no es operativo")

    def build_report(self, project: dict, study: dict, data: dict, results: dict) -> dict:
        """Build the non-binding report structure."""
        raise NotImplementedError("Este módulo aún no es operativo")
