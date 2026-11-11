"""Roda dentro do ambiente do Piper (pesado/venv-piper): sintetiza uma lista de falas.

Uso interno: python piper_lote.py <voz.onnx> <lista.json>
lista.json: [{"texto": ..., "arquivo": ...}, ...]
"""
import json
import sys
import wave

from piper import PiperVoice

voz = PiperVoice.load(sys.argv[1])
for item in json.load(open(sys.argv[2], encoding="utf-8")):
    with wave.open(item["arquivo"], "wb") as saida:
        voz.synthesize_wav(item["texto"], saida)
