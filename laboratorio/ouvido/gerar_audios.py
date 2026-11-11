"""Gera os áudios de teste do ouvido com vozes sintéticas, sem gravar ninguém.

Cada fala de cabeca/casos.py vira um .wav (16 kHz, mono) em cada voz:
a Maria do Windows e quatro vozes brasileiras do Piper. Também sai uma versão
com ruído de fundo, para imitar o microfone de um notebook numa sala.

Uso: python -m laboratorio.ouvido.gerar_audios
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..cabeca.casos import FRASES
from ..comum import PESADO, RESULTADOS

PASTA = RESULTADOS / "audios"
VOZES_PIPER = ["faber-medium", "cadu-medium", "jeff-medium", "edresson-low"]
RUIDO_DB = -24   # volume do ruído; a fala do TTS fica perto de -20 dB, então sobra uns 4 a 8 dB de folga


def falas() -> list[str]:
    vistas = []
    for caso in FRASES:
        if caso["fala"] not in vistas:
            vistas.append(caso["fala"])
    return vistas


def para_16k(origem: Path, destino: Path, ruido: bool = False) -> None:
    comando = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(origem)]
    if ruido:
        comando += ["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=1:seed=7",
                    "-filter_complex",
                    f"[1]volume={RUIDO_DB}dB[r];[0][r]amix=inputs=2:duration=first:normalize=0"]
    comando += ["-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(destino)]
    subprocess.run(comando, check=True)


def gerar_maria(textos: list[str], pasta: Path) -> None:
    lista = pasta / "lista.json"
    lista.write_text(json.dumps([{"texto": t, "arquivo": str(pasta / f"{i:03d}.wav")}
                                 for i, t in enumerate(textos)], ensure_ascii=False), encoding="utf-8")
    script = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Maria Desktop')
$formato = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
foreach ($item in (Get-Content -Raw -Encoding UTF8 '%s' | ConvertFrom-Json)) {
  $s.SetOutputToWaveFile($item.arquivo, $formato)
  $s.Speak($item.texto)
}
$s.SetOutputToNull()
""" % lista
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True)
    lista.unlink()


def gerar_piper(voz: str, textos: list[str], pasta: Path) -> None:
    """Usa o Piper novo (pacote piper-tts), que lê todas as vozes brasileiras."""
    python = PESADO / "venv-piper" / "Scripts" / "python.exe"
    if not python.exists():
        raise SystemExit("Falta o Piper. Rode: python scripts/baixar_laboratorio.py --so piper")
    modelo = PESADO / "modelos" / "vozes" / f"pt_BR-{voz}.onnx"
    lista = pasta / "lista.json"
    lista.write_text(json.dumps([{"texto": t, "arquivo": str(pasta / f"{i:03d}.wav")}
                                 for i, t in enumerate(textos)], ensure_ascii=False), encoding="utf-8")
    subprocess.run([str(python), str(Path(__file__).with_name("piper_lote.py")), str(modelo), str(lista)],
                   check=True)
    lista.unlink()


def main() -> None:
    textos = falas()
    if PASTA.exists():
        shutil.rmtree(PASTA)
    PASTA.mkdir(parents=True)
    (PASTA / "falas.json").write_text(json.dumps(textos, ensure_ascii=False, indent=1), encoding="utf-8")
    vozes = ["maria"] + VOZES_PIPER
    for voz in vozes:
        print(f"voz {voz}: {len(textos)} falas")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            if voz == "maria":
                gerar_maria(textos, tmp)
            else:
                gerar_piper(voz, textos, tmp)
            for condicao, ruido in (("limpo", False), ("ruido", True)):
                destino = PASTA / condicao / voz
                destino.mkdir(parents=True, exist_ok=True)
                for i in range(len(textos)):
                    para_16k(tmp / f"{i:03d}.wav", destino / f"{i:03d}.wav", ruido)
    print(f"Áudios em {PASTA}")


if __name__ == "__main__":
    main()
