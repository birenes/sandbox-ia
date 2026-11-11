"""Teste da cabeça: o modelo pequeno entende o jogador e o robô aprende?

Para cada modelo, sobe o llama-server só no processador e roda:
  1. as frases soltas de casos.FRASES (entendeu certo, ao pé da letra, ou errado);
  2. as aulas inteiras de casos.ROTEIROS (o bolo saiu?).
Mede também o tempo de cada resposta e a memória do servidor.

Uso: python -m laboratorio.cabeca.testar                      (todos os modelos)
     python -m laboratorio.cabeca.testar --modelos Qwen3.5-0.8B
     python -m laboratorio.cabeca.testar --oraculo             (só confere a cozinha)
"""
import argparse
import json
import statistics
import time
from collections import Counter, defaultdict

from ..comum import PESADO, RESULTADOS, ServidorLLM
from .avaliar import TradutorOraculo, classificar, rodar_roteiro, todas_as_linhas
from .casos import FRASES, ROTEIROS
from .tradutor import Tradutor

MODELOS = ["Qwen3.5-0.8B", "Qwen3.5-2B", "Qwen3.5-4B"]


def arquivo_do_modelo(nome: str):
    achados = sorted((PESADO / "modelos" / "llm").glob(f"{nome}-*.gguf"))
    if not achados:
        raise SystemExit(f"Não achei o modelo {nome} em {PESADO / 'modelos' / 'llm'}")
    return achados[0]


def testar_frases(tradutor: Tradutor) -> dict:
    resultados = []
    for caso in FRASES:
        t = tradutor.traduzir(caso["fala"], caso["ensinados"], caso["pergunta"], caso["gravando"])
        classe = classificar(t["pedido"], caso)
        resultados.append({"fala": caso["fala"], "categoria": caso["categoria"], "classe": classe,
                           "pedido": t["pedido"], "segundos": round(t["segundos"], 3),
                           "tokens_gerados": t["tempos"].get("predicted_n")})
        marca = {"certo": "ok", "literal": "ao pé da letra", "errado": "ERRADO"}[classe]
        print(f"  [{marca}] {caso['fala']}  ->  {json.dumps(t['pedido'], ensure_ascii=False)}  "
              f"({t['segundos']:.1f} s)")
    por_categoria = defaultdict(Counter)
    for r in resultados:
        por_categoria[r["categoria"]][r["classe"]] += 1
    return {"casos": resultados,
            "por_categoria": {k: dict(v) for k, v in por_categoria.items()},
            "total": dict(Counter(r["classe"] for r in resultados))}


def testar_roteiros(tradutor) -> list:
    saida = []
    for roteiro in ROTEIROS:
        print(f"  --- aula {roteiro['nome']}: {roteiro['descricao']}")
        saida.append(rodar_roteiro(roteiro, tradutor))
    return saida


def resumo_tempos(segundos: list[float]) -> dict:
    s = sorted(segundos)
    return {"mediana": round(statistics.median(s), 2),
            "p90": round(s[int(len(s) * 0.9) - 1], 2),
            "maximo": round(s[-1], 2)}


def main() -> None:
    p = argparse.ArgumentParser(description="Teste da cabeça do robô.")
    p.add_argument("--modelos", nargs="*", default=MODELOS)
    p.add_argument("--threads", type=int, default=None)
    p.add_argument("--oraculo", action="store_true", help="roda as aulas com entendimento perfeito")
    args = p.parse_args()
    RESULTADOS.mkdir(parents=True, exist_ok=True)

    if args.oraculo:
        for roteiro in ROTEIROS:
            print(f"--- aula {roteiro['nome']}")
            rodar_roteiro(roteiro, TradutorOraculo(todas_as_linhas(roteiro)))
        return

    arquivo = RESULTADOS / "cabeca.json"
    geral = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    for nome in args.modelos:
        print(f"===== {nome}")
        inicio = time.time()
        with ServidorLLM(arquivo_do_modelo(nome), threads=args.threads) as servidor:
            tradutor = Tradutor(servidor)
            # a primeira chamada processa o prompt fixo inteiro; fica guardado para as outras
            aquecimento = tradutor.traduzir("pega o ovo", {})
            frases = testar_frases(tradutor)
            roteiros = testar_roteiros(tradutor)
            memoria = servidor.memoria()
        tempos = [c["segundos"] for c in frases["casos"]]
        geral[nome] = {
            "frases": frases,
            "roteiros": roteiros,
            "memoria_mb": memoria,
            "primeira_resposta_s": round(aquecimento["segundos"], 2),
            "tempo_resposta_s": resumo_tempos(tempos),
            "minutos_de_teste": round((time.time() - inicio) / 60, 1),
        }
        arquivo.write_text(json.dumps(geral, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
        t = frases["total"]
        print(f"  frases: {t.get('certo', 0)} certas, {t.get('literal', 0)} ao pé da letra, "
              f"{t.get('errado', 0)} erradas de {len(FRASES)}")
        for r in roteiros:
            provas = ", ".join(p["bolo"]["resultado"] for p in r["provas"]) or "-"
            print(f"  aula {r['roteiro']}: entendeu {r['entendidas']}/{r['total']}, provas: {provas}")
        print(f"  memória: {memoria}, resposta mediana {geral[nome]['tempo_resposta_s']['mediana']} s")
    print(f"Resultados em {RESULTADOS / 'cabeca.json'}")


if __name__ == "__main__":
    main()
