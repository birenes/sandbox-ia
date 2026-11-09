"""Filma um episódio gravado, usando o Movie Maker do Godot.

O Godot abre uma janela pequena, reproduz o episódio quadro a quadro com fps
fixo e fecha sozinho. O vídeo sai no tamanho pedido mesmo que a tela seja
menor. Se o ffmpeg estiver instalado, sai em .mp4.

Uso: python treino/filmar.py treinos/primeiro/episodios/000123.json
     python treino/filmar.py ... --resolucao 1080x1920   (vertical)
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROJETO = RAIZ / "godot"
JANELA_MAXIMA = (960, 720)  # a janela cabe em qualquer tela; o vídeo não depende dela


def achar_godot(explicito=None):
    candidatos = [explicito, os.environ.get("GODOT")]
    pacotes = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if pacotes.is_dir():
        # a versão _console mostra os erros no terminal
        candidatos += sorted(str(p) for p in pacotes.glob("GodotEngine.GodotEngine_*/Godot_v*_console.exe"))
    candidatos += [shutil.which("godot_console"), shutil.which("godot")]
    for candidato in candidatos:
        if candidato and Path(candidato).exists():
            return candidato
    sys.exit("Não achei o Godot. Passe --godot com o caminho do executável ou defina a variável GODOT.")


def configuracao_de_filmagem(largura, altura):
    """O Godot grava no tamanho da cena, não da janela. Este arquivo temporário
    (override.cfg) muda o tamanho só enquanto a filmagem roda."""
    escala = min(JANELA_MAXIMA[0] / largura, JANELA_MAXIMA[1] / altura, 1.0)
    return (
        "[display]\n\n"
        f"window/size/viewport_width={largura}\n"
        f"window/size/viewport_height={altura}\n"
        f"window/size/window_width_override={int(largura * escala)}\n"
        f"window/size/window_height_override={int(altura * escala)}\n"
        'window/stretch/mode="viewport"\n'
    )


def main():
    p = argparse.ArgumentParser(description="Filma um episódio gravado.")
    p.add_argument("episodio", help="arquivo .json de um episódio guardado pelo mestre")
    p.add_argument("--saida", default=None, help="arquivo de vídeo (padrão: ao lado do episódio, em .mp4)")
    p.add_argument("--resolucao", default="1920x1080", help="largura x altura; 1080x1920 para vertical")
    p.add_argument("--fps", type=int, default=60)
    p.add_argument("--godot", default=None, help="caminho do executável do Godot")
    args = p.parse_args()

    episodio = Path(args.episodio).resolve()
    if not episodio.is_file():
        sys.exit(f"Não achei {episodio}")
    try:
        largura, altura = (int(n) for n in args.resolucao.lower().split("x"))
    except ValueError:
        sys.exit("Use --resolucao no formato 1920x1080")
    saida = Path(args.saida).resolve() if args.saida else episodio.with_suffix(".mp4")
    avi = saida.with_suffix(".avi")

    comando = [
        achar_godot(args.godot),
        "--path", str(PROJETO),
        "--write-movie", avi.as_posix(),
        "--fixed-fps", str(args.fps),
        "res://cenas/replay.tscn",
        "--", f"--episodio={episodio.as_posix()}", "--sair_no_fim",
    ]
    override = PROJETO / "override.cfg"
    if override.exists():
        sys.exit(f"Já existe um {override}. Apague antes de filmar (ele é só temporário).")
    override.write_text(configuracao_de_filmagem(largura, altura), encoding="utf-8")
    try:
        subprocess.run(comando, check=True)
    finally:
        override.unlink(missing_ok=True)

    ffmpeg = shutil.which("ffmpeg")
    if saida.suffix.lower() == ".avi" or not ffmpeg:
        print(f"Vídeo em {avi}")
        return
    subprocess.run([
        ffmpeg, "-y", "-loglevel", "error", "-i", str(avi),
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(saida),
    ], check=True)
    avi.unlink()
    print(f"Vídeo em {saida}")


if __name__ == "__main__":
    main()
