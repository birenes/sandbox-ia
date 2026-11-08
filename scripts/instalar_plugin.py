"""Baixa o plugin Godot RL Agents (licença MIT) e copia para godot/addons.

O plugin não fica no repositório, então cada máquina baixa com este script.
Uso: python scripts/instalar_plugin.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "https://github.com/edbeeching/godot_rl_agents_plugin.git"
RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "godot" / "addons" / "godot_rl_agents"


def main() -> int:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        clone = Path(tmp) / "plugin"
        subprocess.run(["git", "clone", "--depth", "1", REPO, str(clone)], check=True)
        origem = clone / "addons" / "godot_rl_agents"
        if not origem.is_dir():
            print(f"Não achei {origem}. O repositório do plugin mudou de estrutura?")
            return 1
        if DESTINO.exists():
            shutil.rmtree(DESTINO)
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(origem, DESTINO)
    print(f"Plugin instalado em {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
