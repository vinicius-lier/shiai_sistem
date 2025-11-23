"""Script auxiliar para gerar o executável com PyInstaller.

Ele monta os parâmetros corretos de --add-data para Linux e Windows e
inclui o banco SQLite se ele existir no diretório do projeto.
"""
from pathlib import Path
import os

from PyInstaller.__main__ import run


BASE_DIR = Path(__file__).resolve().parent
ADD_DATA_ITEMS = [
    (BASE_DIR / "judocomp", "judocomp"),
    (BASE_DIR / "atletas", "atletas"),
    (BASE_DIR / "categorias_oficiais_judo.json", "categorias_oficiais_judo.json"),
]

sqlite_db = BASE_DIR / "db.sqlite3"
if sqlite_db.exists():
    ADD_DATA_ITEMS.append((sqlite_db, "db.sqlite3"))


def format_add_data(source: Path, target: str) -> str:
    """Formata o argumento --add-data considerando o separador da plataforma."""
    return f"{source}{os.pathsep}{target}"


def main() -> None:
    add_data_args = []
    for source, target in ADD_DATA_ITEMS:
        add_data_args.extend(["--add-data", format_add_data(source, target)])

    run(
        [
            "--onefile",
            "--name",
            "shiai",
            *add_data_args,
            str(BASE_DIR / "launcher.py"),
        ]
    )


if __name__ == "__main__":
    main()
