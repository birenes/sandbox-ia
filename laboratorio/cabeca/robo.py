"""O robô: junta o tradutor, a memória do que foi ensinado e a cozinha.

A memória começa vazia. O que o robô aprende fica aqui, não no modelo de
linguagem: verbos novos (definidos pelo jogador), tarefas gravadas (o jogador
vai mandando e o robô vai fazendo) e cuidados (por onde pegar a faca, a
temperatura do forno, usar luva). As falas do robô são frases prontas, então
nada que ele diz é texto livre gerado pelo modelo.
"""
import json
from pathlib import Path

from .cozinha import PRIMITIVAS, RECIPIENTES, Cozinha

PROFUNDIDADE_MAXIMA = 6


def descrever_passo(p: dict) -> str:
    partes = [p["verbo"]]
    for campo in ("objeto", "destino"):
        if p.get(campo):
            partes.append(p[campo])
    for campo in ("parte", "velocidade"):
        if p.get(campo):
            partes.append(p[campo])
    if p.get("quantidade"):
        partes.append(f"{p['quantidade']}x")
    if p.get("temperatura"):
        partes.append(f"{p['temperatura']} graus")
    if p.get("minutos"):
        partes.append(f"{p['minutos']} min")
    return " ".join(partes)


class Memoria:
    def __init__(self):
        self.verbos: dict[str, dict] = {}
        self.cuidados: dict[str, dict] = {}

    def resumos(self) -> dict:
        saida = {}
        for palavra, d in self.verbos.items():
            if d["origem"] == "tarefa":
                resumo = f"tarefa ensinada pelo jogador ({len(d['passos'])} passos)"
            else:
                exemplo = f" (ex.: {palavra} {d['objeto_exemplo']})" if d.get("objeto_exemplo") else ""
                resumo = exemplo.strip() + " = " + ", ".join(descrever_passo(p) for p in d["passos"])
            saida[palavra] = {"resumo": resumo.strip(" =")}
        return saida

    def salvar(self, caminho: Path) -> None:
        caminho.write_text(json.dumps({"verbos": self.verbos, "cuidados": self.cuidados},
                                      ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def carregar(cls, caminho: Path) -> "Memoria":
        m = cls()
        d = json.loads(caminho.read_text(encoding="utf-8"))
        m.verbos, m.cuidados = d["verbos"], d["cuidados"]
        return m


class Robo:
    def __init__(self, tradutor, memoria: Memoria | None = None, cozinha: Cozinha | None = None):
        self.tradutor = tradutor
        self.memoria = memoria or Memoria()
        self.cozinha = cozinha or Cozinha()
        self.pergunta: str | None = None      # o que o robô acabou de perguntar
        self.pendente: str | None = None      # a fala que ele não entendeu
        self.gravando: str | None = None      # nome da tarefa sendo ensinada
        self.gravacao: list[dict] = []
        self.historico: list[dict] = []

    # ------------------------------------------------------------ ouvir

    def ouvir(self, fala: str, _reouvindo: bool = False) -> dict:
        t = self.tradutor.traduzir(fala, self.memoria.resumos(), self.pergunta, self.gravando)
        pedido = t["pedido"]
        respostas = self._responder(fala, pedido)
        registro = {"fala": fala, "pedido": pedido, "respostas": respostas,
                    "segundos": round(t["segundos"], 3), "reouvindo": _reouvindo}
        self.historico.append(registro)
        return registro

    def _responder(self, fala: str, pedido: dict) -> list[str]:
        tipo = pedido.get("tipo")
        if tipo == "acoes":
            self.pergunta = self.pendente = None
            if self.gravando:
                self.gravacao.extend(pedido["passos"])
            falas = []
            for passo in pedido["passos"]:
                falas += self.executar(passo)
            return falas
        if tipo == "nao_sei":
            palavra = pedido["palavra"]
            self.pergunta = f"Não sei o que é {palavra}. Me explica?"
            self.pendente = fala
            return [self.pergunta]
        if tipo == "definicao":
            palavra = pedido["palavra"].strip()
            if palavra in PRIMITIVAS:
                return [f"Mas eu já sei {palavra}."]
            self.memoria.verbos[palavra] = {
                "origem": "definicao",
                "objeto_exemplo": pedido.get("objeto_exemplo"),
                "passos": pedido["passos"],
                "explicacao": fala,
            }
            falas = [f"Entendi o que é {palavra}."]
            pendente, self.pergunta, self.pendente = self.pendente, None, None
            if pendente:
                r = self.ouvir(pendente, _reouvindo=True)
                falas += r["respostas"]
            return falas
        if tipo == "comecar_tarefa":
            self.gravando, self.gravacao = pedido["nome"].strip(), []
            return ["Tá bom. Vai falando que eu vou fazendo."]
        if tipo == "terminar_tarefa":
            if not self.gravando:
                return ["Mas a gente não estava ensinando nada."]
            nome, self.gravando = self.gravando, None
            if not self.gravacao:
                return ["Você não me mandou fazer nada."]
            self.memoria.verbos[nome] = {"origem": "tarefa", "passos": self.gravacao}
            return [f"Aprendi a {nome}!"]
        if tipo == "cuidado":
            objeto = pedido["objeto"]
            cuidado = {k: v for k, v in pedido.items() if k not in ("tipo", "objeto")}
            if not cuidado:
                return ["Cuidado com o quê?"]
            self.memoria.cuidados.setdefault(objeto, {}).update(cuidado)
            return ["Entendi, vou lembrar."]
        if tipo == "parar":
            self.pergunta = self.pendente = None
            return ["Parei."]
        if tipo == "conversa":
            return ["Hm."]
        return ["Hã?"]

    # ------------------------------------------------------------ fazer

    def executar(self, passo: dict, profundidade: int = 0) -> list[str]:
        if self.cozinha.morto:
            return ["O robô está quebrado e não se mexe."]
        verbo = passo["verbo"]
        if verbo in PRIMITIVAS:
            return self._primitiva(dict(passo))
        if verbo not in self.memoria.verbos:
            return [f"Não sei {verbo}."]
        if profundidade >= PROFUNDIDADE_MAXIMA:
            return ["Me perdi no meio da explicação."]
        d = self.memoria.verbos[verbo]
        vezes = (passo.get("quantidade") or 1) if d["origem"] == "definicao" else 1
        falas = []
        for _ in range(min(vezes, 6)):
            for sub in d["passos"]:
                sub = dict(sub)
                exemplo = d.get("objeto_exemplo")
                if exemplo and passo.get("objeto"):
                    for campo in ("objeto", "destino"):
                        if sub.get(campo) == exemplo:
                            sub[campo] = passo["objeto"]
                falas += self.executar(sub, profundidade + 1)
        return falas

    def _primitiva(self, p: dict) -> list[str]:
        c = self.cozinha
        verbo = p.pop("verbo")
        falas = []
        # "mexe a tigela": a tigela é o destino, não o utensílio
        if verbo == "mexer" and p.get("objeto") in RECIPIENTES and not p.get("destino"):
            p["destino"] = p.pop("objeto")
        # luva, se o jogador ensinou esse cuidado
        envolvidos = {p.get("objeto"), p.get("destino")}
        if verbo == "pegar" and c.onde.get(p.get("objeto") or "") == "forno":
            envolvidos.add("forno")
        precisa_luva = any(self.memoria.cuidados.get(x, {}).get("luva") for x in envolvidos if x)
        if precisa_luva and not c.luva and c.onde.get("luva") == "mesa":
            c.onde["luva"] = "luva_vestida"
            c.luva = True
            falas.append("Vesti a luva antes, como você ensinou.")
        # o corpo pega sozinho o objeto citado antes de usar
        objeto = p.get("objeto")
        if verbo in ("colocar", "despejar", "golpear", "abrir", "mexer") and objeto \
                and objeto not in ("forno", "mesa", "lixo") and c.mao != objeto:
            if c.mao:
                falas.append(f"Estou segurando {c.mao}, não {objeto}.")
                return falas
            falas.append(self._pegar(objeto))
            if c.mao != objeto:
                return falas
        if verbo == "pegar":
            falas.append(self._pegar(objeto, p.get("parte")))
            return falas
        if verbo == "ligar" and not p.get("temperatura"):
            temperatura = self.memoria.cuidados.get("forno", {}).get("temperatura")
            if temperatura:
                p["temperatura"] = temperatura
        if verbo == "mexer":
            p.pop("objeto", None)
        falas.append(c.executar(verbo, **p))
        return falas

    def _pegar(self, objeto, parte=None) -> str:
        if objeto and not parte:
            parte = self.memoria.cuidados.get(objeto, {}).get("parte")
        return self.cozinha.executar("pegar", objeto=objeto, parte=parte)

    # ------------------------------------------------------------ nova partida

    def nova_cozinha(self) -> None:
        """Começa outra partida: cozinha nova, mesma memória."""
        self.cozinha = Cozinha()
        self.pergunta = self.pendente = self.gravando = None
        self.gravacao = []
