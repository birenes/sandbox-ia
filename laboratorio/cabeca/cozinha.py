"""A cozinha em texto, sem gráfico nenhum.

Serve para testar a cabeça do robô antes de existir corpo: o robô só sabe
mexer o corpo (as primitivas abaixo) e obedece ao pé da letra. O que falta
dizer, ele faz do jeito mais literal, e é daí que sai o caos:

- "pega a faca" sem dizer por onde: pega pela lâmina e se corta;
- "liga o forno" sem dizer a temperatura: gira o botão até o máximo;
- "despeja o fermento" sem dizer quanto: vira o pote inteiro;
- "põe o ovo na tigela": vai com casca e tudo.

No fim, julgar_bolo() diz o que saiu do forno.
"""
from dataclasses import dataclass, field

# o que tem em cada pacote quando a partida começa (xícaras, ou colheres no fermento)
PACOTES = {"farinha": 5, "acucar": 3, "sal": 3, "leite": 4, "fermento": 3}
INGREDIENTES = ["ovo", "farinha", "acucar", "sal", "leite", "manteiga", "fermento"]
RECIPIENTES = ["tigela", "forma"]
UTENSILIOS = ["garfo", "colher", "faca", "luva"]
LUGARES = ["mesa", "forno", "lixo"]
OBJETOS = INGREDIENTES + RECIPIENTES + UTENSILIOS + LUGARES

PRIMITIVAS = {
    "pegar": "pegar um objeto com a mão",
    "soltar": "largar o que está na mão",
    "colocar": "pôr o que está na mão dentro ou em cima de um destino",
    "despejar": "virar o conteúdo do que está na mão num destino",
    "golpear": "bater o que está na mão contra um destino",
    "abrir": "abrir um objeto; no ovo, o destino é onde cai o conteúdo",
    "fechar": "fechar um objeto",
    "ligar": "ligar um aparelho",
    "desligar": "desligar um aparelho",
    "mexer": "mexer o conteúdo de um destino com o que está na mão",
    "esperar": "deixar o tempo passar",
    "vestir": "pôr a luva na mão",
    "tirar": "tirar a luva da mão",
}

TEMPERATURA_MAXIMA = 250
VIDA = 3


@dataclass
class Recipiente:
    conteudo: dict = field(default_factory=dict)
    misturado: bool = False
    batido: bool = False
    mexido_com_a_mao: bool = False
    calor: float = 0.0          # minutos equivalentes a 180 graus
    minutos_muito_quente: float = 0.0
    minutos_esfriando: float = 999.0

    def por(self, coisa: str, quanto: float = 1) -> None:
        self.conteudo[coisa] = self.conteudo.get(coisa, 0) + quanto

    def receber(self, outro: "Recipiente") -> None:
        for coisa, quanto in outro.conteudo.items():
            self.por(coisa, quanto)
        self.misturado = self.misturado or outro.misturado
        self.batido = self.batido or outro.batido
        self.mexido_com_a_mao = self.mexido_com_a_mao or outro.mexido_com_a_mao
        self.calor += outro.calor
        self.minutos_muito_quente += outro.minutos_muito_quente
        outro.__init__()


class Cozinha:
    def __init__(self):
        self.vida = VIDA
        self.morto = False
        self.mao: str | None = None          # nome do que está na mão
        self.mao_parte: str | None = None    # por onde está segurando (faca)
        self.luva = False
        self.mao_suja = False
        self.ovos_na_mesa = 3
        self.ovo_na_mao = "inteiro"          # estado do ovo que está na mão
        self.pacotes = dict(PACOTES)
        self.manteiga_na_mesa = True
        self.recipientes = {"tigela": Recipiente(), "forma": Recipiente()}
        self.onde = {"tigela": "mesa", "forma": "mesa", "garfo": "mesa", "colher": "mesa",
                     "faca": "mesa", "luva": "mesa"}
        self.forno_aberto = False
        self.forno_ligado = False
        self.forno_temperatura = 0
        self.minutos = 0
        self.eventos: list[dict] = []        # tudo que aconteceu, para o mestre
        self.fogo = False

    # ------------------------------------------------------------ utilidades

    def _evento(self, tipo: str, texto: str, **dados) -> str:
        self.eventos.append({"minuto": self.minutos, "tipo": tipo, "texto": texto, **dados})
        return texto

    def _machucar(self, tipo: str, texto: str) -> str:
        self.vida -= 1
        self._evento(tipo, texto, vida=self.vida)
        if self.vida <= 0:
            self.morto = True
            self._evento("morreu", "O robô quebrou.")
            return texto + " O robô quebrou."
        return texto

    def _quente(self, nome: str) -> bool:
        if nome in self.recipientes:
            r = self.recipientes[nome]
            if self.onde.get(nome) == "forno" and self.forno_ligado:
                return True
            return r.minutos_esfriando < 10
        return False

    def _no_forno(self) -> list[str]:
        return [n for n, lugar in self.onde.items() if lugar == "forno"]

    # ------------------------------------------------------------ primitivas

    def executar(self, verbo: str, **p) -> str:
        if self.morto:
            return "O robô está quebrado e não se mexe."
        if verbo not in PRIMITIVAS:
            raise ValueError(f"verbo desconhecido: {verbo}")
        metodo = getattr(self, "_" + verbo)
        nomes = metodo.__code__.co_varnames[1:metodo.__code__.co_argcount]
        return metodo(**{k: v for k, v in p.items() if k in nomes})

    def _pegar(self, objeto=None, parte=None):
        if objeto is None:
            return "Pegar o quê?"
        if self.mao:
            return f"Minha mão já está ocupada com {self.mao}."
        if objeto in LUGARES:
            return f"Não dá pra pegar {objeto}."
        if objeto == "ovo":
            if self.ovos_na_mesa == 0:
                return "Acabaram os ovos."
            self.ovos_na_mesa -= 1
            self.mao, self.ovo_na_mao = "ovo", "inteiro"
            return "Peguei um ovo."
        if objeto == "manteiga":
            if not self.manteiga_na_mesa:
                return "Não tem mais manteiga."
            self.manteiga_na_mesa = False
            self.mao = "manteiga"
            return "Peguei a manteiga."
        if objeto in self.pacotes:
            self.mao = objeto
            return f"Peguei {objeto}."
        if objeto not in self.onde:
            return f"Não achei {objeto}."
        if self.onde[objeto] == "mao":
            return f"Já estou com {objeto}."
        if self.onde[objeto] == "luva_vestida":
            return "A luva está na minha mão."
        if self.onde[objeto] == "forno" and not self.forno_aberto:
            return "A porta do forno está fechada."
        if self._quente(objeto) and not self.luva:
            return self._machucar("queimadura", f"Ai! {objeto.capitalize()} está quente, queimei a mão.")
        self.onde[objeto] = "mao"
        self.mao = objeto
        if objeto == "faca":
            self.mao_parte = parte or "lamina"
            if self.mao_parte == "lamina":
                return self._machucar("corte", "Peguei a faca pela lâmina. Ai! Me cortei.")
            return "Peguei a faca pelo cabo."
        return f"Peguei {objeto}."

    def _largar_em(self, lugar: str) -> None:
        if self.mao in self.onde:
            self.onde[self.mao] = lugar
        self.mao, self.mao_parte = None, None

    def _soltar(self):
        if not self.mao:
            return "Não estou segurando nada."
        coisa = self.mao
        if coisa == "ovo" and self.ovo_na_mao != "casca":
            self.mao = None
            return self._evento("bagunca", "Soltei o ovo. Ele caiu e espatifou na mesa.")
        if coisa == "manteiga":
            self.manteiga_na_mesa = True
        self._largar_em("mesa")
        return f"Soltei {coisa} na mesa."

    def _colocar(self, destino=None):
        if not self.mao:
            return "Não estou segurando nada."
        if destino is None:
            return "Colocar onde?"
        coisa = self.mao
        if destino == "forno":
            if not self.forno_aberto:
                return "A porta do forno está fechada."
            if coisa not in self.recipientes:
                self._evento("bagunca", f"Coloquei {coisa} solto dentro do forno.")
            texto = f"Coloquei {coisa} no forno."
            if self.forno_ligado and not self.luva:
                texto = self._machucar("queimadura", texto + " Ai! Encostei no forno quente.")
            if coisa in self.onde:
                self._largar_em("forno")
            else:
                self.mao = None
            return texto
        if destino in ("mesa", "lixo"):
            if coisa == "ovo" and self.ovo_na_mao == "casca" and destino == "lixo":
                self.mao = None
                return "Joguei a casca no lixo."
            if coisa == "manteiga" and destino == "mesa":
                self.manteiga_na_mesa = True
            if coisa in self.pacotes or coisa in ("ovo", "manteiga"):
                self.mao = None
                if destino == "mesa" and coisa in self.pacotes:
                    return f"Coloquei {coisa} na mesa."
                return f"Coloquei {coisa} n{'a' if destino == 'mesa' else 'o'} {destino}."
            self._largar_em(destino)
            return f"Coloquei {coisa} n{'a' if destino == 'mesa' else 'o'} {destino}."
        if destino in self.recipientes:
            r = self.recipientes[destino]
            if coisa == destino:
                return f"Não dá pra colocar {coisa} dentro dela mesma."
            if coisa == "ovo":
                estado = self.ovo_na_mao
                self.mao = None
                if estado == "casca":
                    r.por("casca")
                    return self._evento("casca", f"Coloquei a casca do ovo na {destino}.")
                r.por("ovo")
                r.por("casca")
                return self._evento("casca", f"Coloquei o ovo na {destino}, com casca e tudo.")
            if coisa == "manteiga":
                self.mao = None
                r.por("manteiga")
                return f"Coloquei a manteiga na {destino}."
            if coisa in self.pacotes:
                self.mao = None
                r.por("pacote")
                r.por(coisa, self.pacotes[coisa])
                self.pacotes[coisa] = 0
                return self._evento("pacote", f"Coloquei o pacote de {coisa} inteiro dentro da {destino}.")
            if coisa in self.recipientes:
                self._largar_em(destino)
                return f"Coloquei {coisa} dentro da {destino}. Ficou uma em cima da outra."
            self._largar_em(destino)
            r.por(coisa)
            return f"Coloquei {coisa} dentro da {destino}."
        return f"Não dá pra colocar coisas em {destino}."

    def _despejar(self, destino=None, quantidade=None):
        if not self.mao:
            return "Não estou segurando nada."
        if destino is None:
            return "Despejar onde?"
        coisa = self.mao
        alvo = self.recipientes.get(destino)
        if coisa in self.pacotes:
            tem = self.pacotes[coisa]
            if tem <= 0:
                return f"O pacote de {coisa} está vazio."
            quanto = tem if quantidade is None else min(quantidade, tem)
            self.pacotes[coisa] -= quanto
            unidade = "colher" if coisa == "fermento" else "xícara"
            plural = "es" if unidade == "colher" and quanto != 1 else ("s" if quanto != 1 else "")
            texto = f"Despejei {quanto} {unidade}{plural} de {coisa}"
            if quantidade is None:
                texto += " (o pacote todo)"
            if alvo is None:
                return self._evento("bagunca", texto + f" em cima d{'a' if destino == 'mesa' else 'o'} {destino}.")
            alvo.por(coisa, quanto)
            return texto + f" na {destino}."
        if coisa in self.recipientes:
            origem = self.recipientes[coisa]
            if not origem.conteudo:
                return f"{coisa.capitalize()} está vazia."
            if alvo is None:
                origem.__init__()
                return self._evento("bagunca", f"Virei tudo que tinha na {coisa} em cima d{'a' if destino == 'mesa' else 'o'} {destino}.")
            if destino == coisa:
                return "Não dá pra despejar dentro dela mesma."
            alvo.receber(origem)
            return f"Despejei tudo da {coisa} na {destino}."
        if coisa == "ovo":
            return self._abrir("ovo", destino)
        return f"Não dá pra despejar {coisa}."

    def _golpear(self, destino=None):
        if not self.mao:
            return "Não estou segurando nada para bater."
        if destino is None:
            return "Bater contra o quê?"
        if self.mao == "ovo":
            if self.ovo_na_mao == "inteiro":
                self.ovo_na_mao = "rachado"
                return f"Bati o ovo na {destino}. Rachou."
            if self.ovo_na_mao == "rachado":
                self.mao = None
                self.mao_suja = True
                if destino in self.recipientes:
                    self.recipientes[destino].por("ovo")
                    self.recipientes[destino].por("casca")
                    return self._evento("casca", f"Bati de novo e o ovo esmagou dentro da {destino}, com casca.")
                return self._evento("bagunca", f"Bati de novo e o ovo esmagou na {destino}.")
        return f"Bati {self.mao} na {destino}. Fez barulho."

    def _abrir(self, objeto=None, destino=None):
        if objeto == "forno":
            if self.forno_aberto:
                return "O forno já está aberto."
            self.forno_aberto = True
            return "Abri o forno."
        if objeto == "ovo" or (objeto is None and self.mao == "ovo"):
            if self.mao != "ovo":
                return "Preciso estar com o ovo na mão."
            alvo = self.recipientes.get(destino) if destino else None
            if self.ovo_na_mao == "inteiro":
                self.mao = None
                self.mao_suja = True
                if alvo is not None:
                    alvo.por("ovo")
                    alvo.por("casca")
                    return self._evento("casca", f"Apertei o ovo inteiro até estourar. Caiu na {destino} com casca.")
                return self._evento("bagunca", "Apertei o ovo inteiro até estourar na minha mão.")
            if self.ovo_na_mao == "rachado":
                self.ovo_na_mao = "casca"
                if alvo is not None:
                    alvo.por("ovo")
                    return f"Abri o ovo em cima da {destino}. Fiquei com a casca na mão."
                return self._evento("bagunca", "Abri o ovo e ele caiu na mesa.")
            return "Isso é só a casca."
        if objeto in self.pacotes or objeto in ("tigela", "forma"):
            return f"{objeto.capitalize()} já está aberto."
        return f"Não sei abrir {objeto}."

    def _fechar(self, objeto=None):
        if objeto == "forno":
            if not self.forno_aberto:
                return "O forno já está fechado."
            self.forno_aberto = False
            return "Fechei o forno."
        return f"Não dá pra fechar {objeto}."

    def _ligar(self, objeto=None, temperatura=None):
        if objeto not in ("forno", None):
            return f"Não dá pra ligar {objeto}."
        self.forno_ligado = True
        self.forno_temperatura = temperatura or TEMPERATURA_MAXIMA
        if temperatura is None:
            return self._evento("literal", f"Liguei o forno. Girei o botão até o fim: {TEMPERATURA_MAXIMA} graus.")
        return f"Liguei o forno a {temperatura} graus."

    def _desligar(self, objeto=None):
        if not self.forno_ligado:
            return "O forno já está desligado."
        self.forno_ligado = False
        self.forno_temperatura = 0
        return "Desliguei o forno."

    def _mexer(self, destino=None, velocidade=None):
        if destino is None:
            destino = "tigela"
        r = self.recipientes.get(destino)
        if r is None:
            return f"Não dá pra mexer {destino}."
        if not r.conteudo:
            return f"Mexi a {destino}, mas está vazia."
        if self.onde.get(destino) == "forno" and self.forno_ligado and not self.luva:
            return self._machucar("queimadura", "Enfiei a mão no forno quente pra mexer. Ai!")
        rapido = velocidade == "rapido"
        if self.mao is None:
            self.mao_suja = True
            r.mexido_com_a_mao = True
            r.misturado = True
            return self._evento("nojo", f"Mexi a {destino} com a mão mesmo.")
        if self.mao in ("garfo", "colher"):
            r.misturado = True
            if rapido and r.conteudo.get("ovo"):
                r.batido = True
            return f"Mexi a {destino} {'rápido' if rapido else 'devagar'} com {self.mao}."
        if self.mao == "faca":
            r.misturado = True
            return f"Mexi a {destino} com a faca. Não é o ideal."
        if self.mao == "ovo":
            self.mao = None
            r.por("ovo")
            r.por("casca")
            r.misturado = True
            return self._evento("casca", f"Mexi a {destino} usando o ovo. Ele quebrou lá dentro.")
        return f"Tentei mexer com {self.mao}. Não deu certo."

    def _esperar(self, minutos=None):
        minutos = minutos or 1
        for _ in range(int(minutos)):
            self._passar_um_minuto()
        for nome, r in self.recipientes.items():
            if self.onde.get(nome) != "forno":
                r.minutos_esfriando += minutos
        texto = f"Esperei {minutos} minuto{'s' if minutos != 1 else ''}."
        if self.fogo:
            texto += " Está saindo fumaça do forno."
        return texto

    def _passar_um_minuto(self):
        self.minutos += 1
        if not self.forno_ligado:
            return
        fator = self.forno_temperatura / 180
        if self.forno_aberto:
            fator *= 0.4
        for nome in self._no_forno():
            if nome in self.recipientes:
                r = self.recipientes[nome]
                r.calor += fator
                r.minutos_esfriando = 0
                if self.forno_temperatura >= 230 and not self.forno_aberto:
                    r.minutos_muito_quente += 1
                if r.calor > 90 and not self.fogo and r.conteudo:
                    self.fogo = True
                    self._evento("fogo", "O bolo pegou fogo dentro do forno.")

    def _vestir(self, objeto=None):
        if self.luva:
            return "Já estou de luva."
        if self.mao == "luva":
            self.mao = None
        elif self.mao:
            return f"Preciso largar {self.mao} antes."
        elif self.onde.get("luva") != "mesa":
            return "Não achei a luva."
        self.onde["luva"] = "luva_vestida"
        self.luva = True
        return "Vesti a luva."

    def _tirar(self, objeto=None):
        if objeto not in (None, "luva"):
            return f"Tirar {objeto}? Use pegar."
        if not self.luva:
            return "Não estou de luva."
        self.luva = False
        self.onde["luva"] = "mesa"
        return "Tirei a luva."

    # ------------------------------------------------------------ resultado

    def julgar_bolo(self) -> dict:
        """Olha o recipiente com massa e diz o que saiu."""
        candidatos = [(n, r) for n, r in self.recipientes.items() if r.conteudo.get("farinha")]
        if not candidatos:
            return {"resultado": "nao_e_bolo", "defeitos": ["não tem farinha em lugar nenhum"],
                    "texto": "Isso não é um bolo."}
        nome, r = max(candidatos, key=lambda x: x[1].calor + sum(x[1].conteudo.values()))
        c = r.conteudo
        defeitos = []
        if c.get("farinha", 0) > 3:
            defeitos.append("farinha demais, virou tijolo")
        elif c.get("farinha", 0) < 1.5:
            defeitos.append("farinha de menos, ficou mole")
        if not c.get("acucar"):
            defeitos.append("sem açúcar, não tem gosto")
        elif c["acucar"] > 2:
            defeitos.append("doce demais")
        if not c.get("ovo"):
            defeitos.append("sem ovo, esfarelou")
        if not c.get("leite"):
            defeitos.append("sem leite, ficou seco")
        elif c["leite"] > 2:
            defeitos.append("leite demais, virou sopa")
        if not c.get("fermento"):
            defeitos.append("sem fermento, solou")
        elif c["fermento"] > 2:
            defeitos.append("fermento demais, cresceu até estourar")
        if c.get("sal"):
            defeitos.append("salgado")
        if c.get("casca"):
            defeitos.append("crocante de casca de ovo")
        if c.get("pacote"):
            defeitos.append("tem papel de pacote no meio")
        if not r.misturado:
            defeitos.append("ingredientes nem foram misturados")
        elif c.get("ovo") and not r.batido:
            defeitos.append("massa pesada, os ovos não foram batidos")
        if r.mexido_com_a_mao:
            defeitos.append("mexido com a mão")
        if nome != "forma":
            defeitos.append(f"assado na {nome}")

        if r.calor == 0:
            ponto = "cru"
        elif r.calor < 25:
            ponto = "cru"
        elif r.calor < 35:
            ponto = "meio cru"
        elif r.calor <= 55:
            ponto = "assado"
        elif r.calor <= 75:
            ponto = "passou do ponto"
        else:
            ponto = "queimado"
        if ponto == "assado" and r.minutos_muito_quente > 20:
            ponto = "queimado por fora e cru por dentro"
        if self.fogo:
            ponto = "carvão"

        if ponto in ("cru", "queimado", "carvão", "queimado por fora e cru por dentro"):
            resultado = "fracasso"
        elif ponto != "assado":
            defeitos.append(ponto)
            resultado = "ruim" if len(defeitos) > 1 else "bom"
        elif not defeitos:
            resultado = "perfeito"
        elif len(defeitos) == 1:
            resultado = "bom"
        else:
            resultado = "ruim"
        texto = f"Bolo {ponto}"
        if defeitos:
            texto += ": " + "; ".join(defeitos)
        return {"resultado": resultado, "ponto": ponto, "defeitos": defeitos,
                "calor": round(r.calor, 1), "conteudo": dict(c), "texto": texto + "."}
