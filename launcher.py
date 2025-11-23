"""Ponto de entrada simples para empacotar a aplicação com PyInstaller.

Executa o servidor de desenvolvimento do Django na porta 8000. Ao gerar
executáveis com PyInstaller, use este arquivo como script principal.
"""

import os
import sys
from pathlib import Path

from django.core.management import execute_from_command_line


def main():
    base_dir = Path(__file__).resolve().parent
    sys.path.append(str(base_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "judocomp.settings")

    execute_from_command_line(["manage.py", "runserver", "0.0.0.0:8000"])


if __name__ == "__main__":
    main()
