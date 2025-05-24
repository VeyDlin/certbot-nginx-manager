import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Paths:
    nginx: Path
    template: Path
    acme_template: Path


@dataclass
class Config:
    domain: str
    email: str
    cron_days: int
    paths: Paths

    @staticmethod
    def load_from_file(path: Path) -> "Config":
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return Config(
            domain=data["domain"],
            email=data["email"],
            cron_days=int(data["cron_days"]),
            paths=Paths(
                nginx=Path(data["paths"]["nginx"]),
                template=Path(data["paths"]["template"]),
                acme_template=Path(data["paths"]["acme_template"]),
            )
        )