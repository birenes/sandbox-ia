"""Compara o que o tradutor respondeu com o que era esperado, e roda aulas inteiras."""
import unicodedata

from .robo import Memoria, Robo

PARAMETROS = ("quantidade", "temperatura", "minutos", "parte", "velocidade")


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").strip()


def _passo_confere(obtido: dict, esperado: dict) -> bool:
    for campo, valor in esperado.items():
        if valor is None:
            if obtido.get(campo) is not None:
                return False
        elif obtido.get(campo) != valor:
            return False
    # inventar quantidade, temperatura etc. que o jogador não disse estraga a piada
    for campo in PARAMETROS:
        if campo not in esperado and obtido.get(campo) is not None:
            return False
    return True


def _passos_conferem(obtidos: list, esperados: list) -> bool:
    return len(obtidos) == len(esperados) and all(
        _passo_confere(o, e) for o, e in zip(obtidos, esperados))


def confere(pedido: dict, esperado: dict) -> bool:
    if pedido.get("tipo") != esperado["tipo"]:
        return False
    tipo = esperado["tipo"]
    if tipo == "acoes":
        return _passos_conferem(pedido.get("passos", []), esperado["passos"])
    if tipo == "nao_sei":
        palavras = esperado["palavra"]
        palavras = palavras if isinstance(palavras, list) else [palavras]
        obtida = normalizar(pedido.get("palavra"))
        return any(normalizar(p) in obtida for p in palavras)
    if tipo == "definicao":
        if normalizar(pedido.get("palavra")) != normalizar(esperado["palavra"]):
            return False
        return _passos_conferem(pedido.get("passos", []), esperado["passos"])
    if tipo == "comecar_tarefa":
        return normalizar(esperado.get("nome", "")) in normalizar(pedido.get("nome"))
    if tipo == "cuidado":
        return all(pedido.get(k) == v for k, v in esperado.items())
    return True


def classificar(pedido: dict, caso: dict) -> str:
    if any(confere(pedido, e) for e in caso["aceitas"]):
        return "certo"
    if any(confere(pedido, e) for e in caso.get("literal", [])):
        return "literal"
    return "errado"


class TradutorOraculo:
    """Responde exatamente o esperado de cada fala. Serve para conferir que a
    cozinha e a memória levam ao bolo certo quando o entendimento é perfeito."""

    def __init__(self, linhas: list[dict]):
        self.linhas = {l["fala"]: l for l in linhas}

    def traduzir(self, fala, ensinados, pergunta=None, gravando=None):
        l = self.linhas[fala]
        pedido = l["esperado"]
        if pedido["tipo"] == "nao_sei" and l.get("depois"):
            if any(normalizar(p) in map(normalizar, ensinados) for p in pedido["palavra"]):
                pedido = l["depois"]
        if pedido["tipo"] == "nao_sei":
            pedido = {"tipo": "nao_sei", "palavra": pedido["palavra"][0]}
        return {"pedido": pedido, "segundos": 0.0, "tempos": {}}


def todas_as_linhas(roteiro: dict) -> list[dict]:
    linhas = list(roteiro["ensino"])
    for prova in roteiro["provas"]:
        linhas += prova["antes"] + [prova["fala"]]
    return linhas


def rodar_roteiro(roteiro: dict, tradutor, mostrar=print) -> dict:
    """Uma aula inteira: ensina, depois começa cozinhas novas e pede a tarefa."""
    robo = Robo(tradutor, Memoria())
    falas = []

    def falar(linha):
        r = robo.ouvir(linha["fala"])
        esperado = linha["esperado"]
        ok = confere(r["pedido"], esperado) if not r.get("reouvindo") else None
        falas.append({**r, "esperado": esperado, "confere": ok})
        mostrar(f"  jogador: {linha['fala']}")
        mostrar(f"    robô: {' | '.join(r['respostas'])}{'' if ok else '   <- entendeu diferente'}")

    for linha in roteiro["ensino"]:
        falar(linha)
    resultado_ensino = robo.cozinha.julgar_bolo()
    acidentes_ensino = [e for e in robo.cozinha.eventos if e["tipo"] in ("corte", "queimadura", "morreu", "fogo")]

    provas = []
    for prova in roteiro["provas"]:
        for linha in prova["antes"]:
            falar(linha)
        robo.nova_cozinha()
        mostrar("  (cozinha nova)")
        falar(prova["fala"])
        bolo = robo.cozinha.julgar_bolo()
        mostrar(f"    => {bolo['texto']}")
        provas.append({"fala": prova["fala"]["fala"], "bolo": bolo,
                       "eventos": robo.cozinha.eventos, "vida": robo.cozinha.vida})

    verificado = None
    if roteiro.get("verificar"):
        ultimas = " ".join(falas[-1]["respostas"])
        verificado = roteiro["verificar"] in ultimas

    conferidas = [f for f in falas if f["confere"] is not None]
    return {
        "roteiro": roteiro["nome"],
        "falas": falas,
        "entendidas": sum(1 for f in conferidas if f["confere"]),
        "total": len(conferidas),
        "bolo_na_aula": resultado_ensino,
        "acidentes_na_aula": acidentes_ensino,
        "provas": provas,
        "verificado": verificado,
        "memoria": {"verbos": robo.memoria.verbos, "cuidados": robo.memoria.cuidados},
        "segundos": [f["segundos"] for f in falas],
    }
