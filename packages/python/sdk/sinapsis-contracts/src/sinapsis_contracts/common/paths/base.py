from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _ApiPaths:
    api: str = "/api"
    version: str = "/v1"

    @property
    def base(self) -> str:
        return f"{self.api}{self.version}"

    @staticmethod
    def render(template: str, *, base: str = "", **params: str) -> str:
        template = f"{base}{template}"

        for name, value in params.items():
            template = template.replace(f"{{{name}:path}}", value)
            template = template.replace(f"{{{name}}}", value)

        return template


BaseApiPaths = _ApiPaths()
