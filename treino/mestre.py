"""Agente mestre: observa todos os episódios, marca o que foge do normal e
escreve um diário de bordo. É daí que saem os trechos para o vídeo.

Ele não olha imagem. Cada arena do Godot grava o próprio episódio (trajetória
e eventos) e entrega no fim. O mestre julga com regras simples, guarda inteiros
os episódios marcados e só uma amostra dos normais. Depois, qualquer episódio
guardado pode ser filmado com o treino/filmar.py.

Durante o treino ele roda dentro do treinar.py. Também roda sozinho, sobre
episódios já gravados (por exemplo, pelo Godot com --gravar_em):

    python treino/mestre.py caminho/episodios.jsonl --saida treinos/analise
"""
import argparse
import json
import math
import statistics
from collections import deque
from pathlib import Path

JANELA_TAXA = 100             # episódios usados para medir a taxa de acerto
MARCOS_DE_TAXA = (0.10, 0.25, 0.50, 0.75, 0.90)
JANELA_PONTOS = 200           # episódios usados para saber o que é "normal"
MINIMO_PARA_COMPARAR = 50     # antes disso, não dá para dizer o que é fora da curva
LIMITE_FORA_DA_CURVA = 3.0    # desvios-padrão
BATIDAS_DEMAIS = 5
PARADO_ATE_METROS = 1.0
CIRCULO_CAMINHO_MINIMO = 15.0
CIRCULO_DESLOCAMENTO_MAXIMO = 3.0
MELHORA_PARA_RECORDE = 0.9    # recorde só conta se for 10% mais rápido
QUEDA_PREOCUPANTE = 0.20      # taxa caiu 20 pontos depois de passar de 50%
AMOSTRA_DE_NORMAIS = 50       # guarda 1 a cada tantos episódios normais

RESULTADOS = {
    "acertou": "chegou no alvo",
    "tempo_esgotado": "tempo esgotado",
    "saiu_da_arena": "saiu da arena",
    "interrompido": "interrompido",
}


def numero_br(valor, casas=1):
    """1234.5 vira "1.234,5"."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


class Mestre:
    def __init__(self, pasta):
        self.pasta = Path(pasta)
        self.pasta_episodios = self.pasta / "episodios"
        self.pasta_amostra = self.pasta_episodios / "amostra"
        self.pasta_amostra.mkdir(parents=True, exist_ok=True)
        self.diario = self.pasta / "diario.md"
        self.diario_dados = self.pasta / "diario.jsonl"
        if not self.diario.exists():
            self.diario.write_text("# Diário de bordo\n\n", encoding="utf-8")

        self.total = 0
        self.acertos = 0
        self.marcados = 0
        self.resultados = deque(maxlen=JANELA_TAXA)
        self.pontos = deque(maxlen=JANELA_PONTOS)
        self.batidas = deque(maxlen=JANELA_PONTOS)
        self.melhor_tempo = None
        self.marcos_batidos = set()
        self.melhor_taxa = 0.0
        self.em_queda = False
        self.normais_sem_amostra = 0

    # -- entrada ---------------------------------------------------------------

    def receber(self, episodio, passo_treino):
        """Julga um episódio. Devolve a lista de motivos (vazia se for normal)."""
        if episodio.get("resultado") == "interrompido":
            return []
        self.total += 1
        ep = dict(episodio)
        ep["id"] = self.total
        ep["passo_treino"] = int(passo_treino)

        motivos = self._marcos(ep) + self._anomalias(ep) + self._fora_da_curva(ep)
        self._atualizar(ep)
        motivos += self._marcos_de_taxa()

        if motivos:
            self.marcados += 1
            ep["motivos"] = motivos
            self._guardar(ep, self.pasta_episodios)
            self._anotar(ep, motivos)
        else:
            self.normais_sem_amostra += 1
            if self.normais_sem_amostra >= AMOSTRA_DE_NORMAIS:
                self.normais_sem_amostra = 0
                self._guardar(ep, self.pasta_amostra)
        return motivos

    def taxa(self):
        if not self.resultados:
            return None
        return sum(self.resultados) / len(self.resultados)

    # -- regras ----------------------------------------------------------------

    def _marcos(self, ep):
        motivos = []
        if ep["resultado"] != "acertou":
            return motivos
        tempo = ep["duracao_s"]
        if self.acertos == 0:
            motivos.append(f"primeiro acerto da história ({numero_br(tempo)} s)")
        elif self.melhor_tempo is not None and tempo < self.melhor_tempo * MELHORA_PARA_RECORDE:
            motivos.append(
                f"recorde de tempo: {numero_br(tempo)} s (antes {numero_br(self.melhor_tempo)} s)"
            )
        return motivos

    def _anomalias(self, ep):
        motivos = []
        if ep["resultado"] == "saiu_da_arena":
            motivos.append("saiu da arena (provável bug de física)")
        if ep["resultado"] == "tempo_esgotado":
            caminho, deslocamento = medir_trajetoria(ep.get("trajetoria", []))
            if caminho < PARADO_ATE_METROS:
                motivos.append("ficou parado o episódio inteiro")
            elif caminho > CIRCULO_CAMINHO_MINIMO and deslocamento < CIRCULO_DESLOCAMENTO_MAXIMO:
                motivos.append(
                    f"andou {numero_br(caminho)} m e terminou a "
                    f"{numero_br(deslocamento)} m de onde começou (rodando em círculo?)"
                )
        return motivos

    def _fora_da_curva(self, ep):
        """Compara com os episódios recentes: o que é normal muda ao longo do treino."""
        motivos = []
        z = desvios(self.pontos, ep["pontos"])
        if z is not None and abs(z) >= LIMITE_FORA_DA_CURVA:
            lado = "acima" if z > 0 else "abaixo"
            motivos.append(
                f"pontuação muito {lado} do normal ({numero_br(ep['pontos'], 2)}, "
                f"média recente {numero_br(statistics.fmean(self.pontos), 2)})"
            )
        batidas = contar_batidas(ep)
        z = desvios(self.batidas, batidas)
        if batidas >= BATIDAS_DEMAIS and z is not None and z >= LIMITE_FORA_DA_CURVA:
            motivos.append(
                f"bateu na parede {batidas} vezes "
                f"(o normal agora é {numero_br(statistics.fmean(self.batidas))})"
            )
        return motivos

    def _marcos_de_taxa(self):
        if len(self.resultados) < JANELA_TAXA:
            return []
        taxa = self.taxa()
        motivos = []
        novos = [m for m in MARCOS_DE_TAXA if taxa >= m and m not in self.marcos_batidos]
        if novos:
            # se passou de vários de uma vez, conta só o maior
            self.marcos_batidos.update(novos)
            motivos.append(f"taxa de acerto passou de {max(novos):.0%}")
        self.melhor_taxa = max(self.melhor_taxa, taxa)
        if self.melhor_taxa >= 0.5 and taxa <= self.melhor_taxa - QUEDA_PREOCUPANTE and not self.em_queda:
            self.em_queda = True
            motivos.append(f"piorou: taxa caiu de {self.melhor_taxa:.0%} para {taxa:.0%}")
        elif self.em_queda and taxa >= self.melhor_taxa - 0.05:
            self.em_queda = False
            motivos.append(f"se recuperou: taxa voltou a {taxa:.0%}")
        return motivos

    # -- estado e registro -----------------------------------------------------

    def _atualizar(self, ep):
        acertou = ep["resultado"] == "acertou"
        self.resultados.append(1 if acertou else 0)
        self.pontos.append(ep["pontos"])
        self.batidas.append(contar_batidas(ep))
        if acertou:
            self.acertos += 1
            if self.melhor_tempo is None or ep["duracao_s"] < self.melhor_tempo:
                self.melhor_tempo = ep["duracao_s"]

    def _guardar(self, ep, pasta):
        arquivo = pasta / f"{ep['id']:06d}.json"
        arquivo.write_text(json.dumps(ep, ensure_ascii=False), encoding="utf-8")

    def _anotar(self, ep, motivos):
        cabecalho = (
            f"passo {numero_br(ep['passo_treino'], 0)}: {ep['arena']}, "
            f"episódio {ep['numero']} (arquivo {ep['id']:06d}.json), "
            f"{RESULTADOS.get(ep['resultado'], ep['resultado'])} em {numero_br(ep['duracao_s'])} s"
        )
        with self.diario.open("a", encoding="utf-8") as f:
            f.write(f"- {cabecalho}\n")
            for motivo in motivos:
                f.write(f"  - {motivo}\n")
        with self.diario_dados.open("a", encoding="utf-8") as f:
            linha = {k: ep[k] for k in ("id", "passo_treino", "arena", "numero", "resultado", "duracao_s", "pontos")}
            linha["motivos"] = motivos
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def desvios(janela, valor):
    """Quantos desvios-padrão o valor está da média da janela (None se ainda é cedo)."""
    if len(janela) < MINIMO_PARA_COMPARAR:
        return None
    media = statistics.fmean(janela)
    desvio = statistics.pstdev(janela)
    if desvio == 0:
        return 0.0 if valor == media else math.copysign(math.inf, valor - media)
    return (valor - media) / desvio


def contar_batidas(ep):
    return sum(1 for e in ep.get("eventos", []) if e["tipo"] == "bateu_na_parede")


def medir_trajetoria(trajetoria):
    """Comprimento do caminho no chão e distância entre o começo e o fim."""
    if len(trajetoria) < 2:
        return 0.0, 0.0
    caminho = 0.0
    for a, b in zip(trajetoria, trajetoria[1:]):
        caminho += math.hypot(b[0] - a[0], b[2] - a[2])
    inicio, fim = trajetoria[0], trajetoria[-1]
    return caminho, math.hypot(fim[0] - inicio[0], fim[2] - inicio[2])


def criar_callback(pasta):
    """Versão do mestre que roda dentro do treino do Stable-Baselines3."""
    from stable_baselines3.common.callbacks import BaseCallback

    class MestreCallback(BaseCallback):
        def __init__(self):
            super().__init__()
            self.mestre = Mestre(pasta)

        def _on_step(self):
            for info in self.locals.get("infos", []):
                for episodio in info.get("episodios", []):
                    self.mestre.receber(episodio, self.num_timesteps)
            taxa = self.mestre.taxa()
            if taxa is not None:
                self.logger.record("mestre/taxa_de_acerto", taxa)
            self.logger.record("mestre/episodios_marcados", self.mestre.marcados)
            return True

    return MestreCallback()


def main():
    p = argparse.ArgumentParser(description="Roda o mestre sobre episódios já gravados.")
    p.add_argument("episodios", help="arquivo .jsonl, um episódio por linha")
    p.add_argument("--saida", required=True, help="pasta onde ficam o diário e os episódios marcados")
    args = p.parse_args()

    mestre = Mestre(args.saida)
    with open(args.episodios, encoding="utf-8") as f:
        for indice, linha in enumerate(f, start=1):
            if linha.strip():
                mestre.receber(json.loads(linha), indice)
    taxa = mestre.taxa()
    print(f"{mestre.total} episódios, {mestre.marcados} marcados, "
          f"taxa de acerto recente {taxa:.0%}" if taxa is not None else "nenhum episódio")
    print(f"Diário em {Path(args.saida) / 'diario.md'}")


if __name__ == "__main__":
    main()
