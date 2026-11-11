"""Caminhos e utilidades usados pelos testes do laboratório."""
import ctypes
import json
import os
import subprocess
import time
import urllib.request
from ctypes import wintypes
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PESADO = Path(os.environ.get("SANDBOX_PESADO", RAIZ / "pesado"))
RESULTADOS = RAIZ / "laboratorio" / "resultados"


def achar_programa(pasta: str, nome: str) -> Path:
    """Acha um executável dentro de pesado/bin/<pasta>, em qualquer subpasta."""
    achados = sorted((PESADO / "bin" / pasta).rglob(nome))
    if not achados:
        raise SystemExit(f"Não achei {nome} em {PESADO / 'bin' / pasta}. "
                         "Rode antes: python scripts/baixar_laboratorio.py")
    return achados[0]


# ---------------------------------------------------------------- memória (Windows)

class _Contadores(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def memoria_mb(pid: int) -> dict:
    """Memória de um processo em MB: em uso agora e o pico."""
    kernel = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return {"agora": None, "pico": None}
    try:
        c = _Contadores()
        c.cb = ctypes.sizeof(c)
        psapi.GetProcessMemoryInfo(handle, ctypes.byref(c), c.cb)
        return {"agora": round(c.WorkingSetSize / 1e6), "pico": round(c.PeakWorkingSetSize / 1e6)}
    finally:
        kernel.CloseHandle(handle)


# ---------------------------------------------------------------- servidor do modelo

class ServidorLLM:
    """Sobe o llama-server com um modelo e conversa com ele por HTTP.

    Só processador por padrão (gpu=0), porque a ideia é rodar em qualquer PC.
    """

    def __init__(self, modelo: Path, porta: int = 8090, threads: int | None = None,
                 contexto: int = 4096, gpu: int = 0):
        self.modelo = modelo
        self.porta = porta
        self.url = f"http://127.0.0.1:{porta}"
        comando = [
            str(achar_programa("llama", "llama-server.exe")),
            "-m", str(modelo),
            "--port", str(porta),
            "-c", str(contexto),
            "-ngl", str(gpu),
            "--jinja",
            "--reasoning-budget", "0",
            "--no-webui",
        ]
        if threads:
            comando += ["-t", str(threads)]
        RESULTADOS.mkdir(parents=True, exist_ok=True)
        self.log = open(RESULTADOS / f"llama-server-{modelo.stem}.log", "w", encoding="utf-8")
        self.processo = subprocess.Popen(comando, stdout=self.log, stderr=subprocess.STDOUT)
        self._esperar()

    def _esperar(self, limite: float = 180) -> None:
        inicio = time.time()
        while time.time() - inicio < limite:
            if self.processo.poll() is not None:
                raise RuntimeError(f"llama-server fechou; veja {self.log.name}")
            try:
                with urllib.request.urlopen(self.url + "/health", timeout=2) as r:
                    if json.load(r).get("status") == "ok":
                        return
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError("llama-server não respondeu")

    def conversar(self, mensagens: list, esquema: dict | None = None, max_tokens: int = 400) -> dict:
        corpo = {
            "messages": mensagens,
            "temperature": 0,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        if esquema:
            corpo["response_format"] = {"type": "json_schema", "json_schema": {"schema": esquema}}
        pedido = urllib.request.Request(
            self.url + "/v1/chat/completions",
            data=json.dumps(corpo).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        inicio = time.perf_counter()
        with urllib.request.urlopen(pedido, timeout=300) as r:
            resposta = json.load(r)
        segundos = time.perf_counter() - inicio
        return {
            "texto": resposta["choices"][0]["message"]["content"],
            "segundos": segundos,
            "tokens": resposta.get("usage", {}),
            "tempos": resposta.get("timings", {}),
        }

    def memoria(self) -> dict:
        return memoria_mb(self.processo.pid)

    def fechar(self) -> None:
        self.processo.terminate()
        try:
            self.processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.processo.kill()
        self.log.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()
