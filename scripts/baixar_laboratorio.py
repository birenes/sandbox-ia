"""Baixa o que os testes do laboratório precisam: llama.cpp, whisper.cpp, Piper,
os modelos de linguagem, os modelos de fala e as vozes.

O Piper (vozes de teste) vai num ambiente Python à parte.
Tudo vai para a pasta pesado/ (ou para SANDBOX_PESADO, se definida), que fica
fora do git. São uns 6 GB. Rodar de novo só baixa o que falta.

Uso: python scripts/baixar_laboratorio.py
     python scripts/baixar_laboratorio.py --so llm whisper
"""
import argparse
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from laboratorio.comum import PESADO  # noqa: E402

LLAMA_CPP = "b12242"
WHISPER_CPP = "b5454"
PIPER = "piper-tts==1.3.0"

HF = "https://huggingface.co"
GH = "https://github.com"

# grupo: [(url, destino relativo a PESADO, descompactar?)]
ARQUIVOS = {
    "programas": [
        (f"{GH}/ggml-org/llama.cpp/releases/download/{LLAMA_CPP}/llama-{LLAMA_CPP}-bin-win-cpu-x64.zip",
         "bin/llama", True),
        (f"{GH}/ggml-org/whisper.cpp/releases/download/{WHISPER_CPP}/whisper-bin-x64.zip",
         "bin/whisper", True),
    ],
    "llm": [
        (f"{HF}/lmstudio-community/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-Q4_K_M.gguf",
         "modelos/llm/Qwen3.5-0.8B-Q4_K_M.gguf", False),
        (f"{HF}/lmstudio-community/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-Q4_K_M.gguf",
         "modelos/llm/Qwen3.5-2B-Q4_K_M.gguf", False),
        (f"{HF}/lmstudio-community/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf",
         "modelos/llm/Qwen3.5-4B-Q4_K_M.gguf", False),
    ],
    "whisper": [
        (f"{HF}/ggerganov/whisper.cpp/resolve/main/ggml-base.bin", "modelos/whisper/ggml-base.bin", False),
        (f"{HF}/ggerganov/whisper.cpp/resolve/main/ggml-small.bin", "modelos/whisper/ggml-small.bin", False),
        (f"{HF}/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin",
         "modelos/whisper/ggml-large-v3-turbo-q5_0.bin", False),
    ],
    "vozes": [
        (f"{HF}/rhasspy/piper-voices/resolve/main/pt/pt_BR/{voz}/{q}/pt_BR-{voz}-{q}.onnx{ext}",
         f"modelos/vozes/pt_BR-{voz}-{q}.onnx{ext}", False)
        for voz, q in [("faber", "medium"), ("cadu", "medium"), ("jeff", "medium"), ("edresson", "low")]
        for ext in ("", ".json")
    ],
}


def baixar(url: str, destino: Path) -> None:
    temporario = destino.with_name(destino.name + ".parcial")
    temporario.parent.mkdir(parents=True, exist_ok=True)
    pedido = urllib.request.Request(url, headers={"User-Agent": "sandbox-ia"})
    with urllib.request.urlopen(pedido) as resposta, open(temporario, "wb") as saida:
        total = int(resposta.headers.get("Content-Length") or 0)
        feito = 0
        while bloco := resposta.read(1 << 20):
            saida.write(bloco)
            feito += len(bloco)
            if total:
                print(f"\r  {destino.name}: {feito / 1e6:.0f} de {total / 1e6:.0f} MB", end="", flush=True)
    print()
    temporario.replace(destino)


def instalar_piper() -> None:
    """O Piper novo é um pacote Python; fica num ambiente separado em pesado/venv-piper."""
    ambiente = PESADO / "venv-piper"
    python = ambiente / "Scripts" / "python.exe"
    if python.exists():
        print("  venv-piper: já existe")
        return
    subprocess.run([sys.executable, "-m", "venv", str(ambiente)], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-q", PIPER], check=True)
    print("  venv-piper: pronto")


def main() -> None:
    p = argparse.ArgumentParser(description="Baixa programas e modelos do laboratório.")
    p.add_argument("--so", nargs="*", choices=list(ARQUIVOS) + ["piper"], help="baixa só estes grupos")
    args = p.parse_args()

    for grupo in args.so or list(ARQUIVOS) + ["piper"]:
        print(f"[{grupo}]")
        if grupo == "piper":
            instalar_piper()
            continue
        for url, relativo, descompactar in ARQUIVOS[grupo]:
            destino = PESADO / relativo
            if descompactar:
                pronto = destino / ".ok"
                if pronto.exists():
                    print(f"  {relativo}: já existe")
                    continue
                zip_ = PESADO / "baixando" / Path(url).name
                baixar(url, zip_)
                if destino.exists():
                    shutil.rmtree(destino)
                with zipfile.ZipFile(zip_) as z:
                    z.extractall(destino)
                zip_.unlink()
                pronto.write_text(url, encoding="utf-8")
            else:
                if destino.exists():
                    print(f"  {relativo}: já existe")
                    continue
                baixar(url, destino)
    print(f"Pronto. Tudo em {PESADO}")


if __name__ == "__main__":
    main()
