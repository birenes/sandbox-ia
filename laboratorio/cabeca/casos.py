"""Casos de teste da cabeça.

FRASES: falas soltas com a resposta certa (ou as respostas aceitáveis).
ROTEIROS: aulas inteiras, do robô sem saber nada até o bolo pronto.

Num caso, "literal" marca uma resposta aceitável que é a leitura ao pé da
letra (ex.: "bate os ovos" virar golpear os ovos). Não é erro, é a piada,
mas conta à parte.
"""


def P(verbo, **campos):
    return {"verbo": verbo, **campos}


def acoes(*passos):
    return {"tipo": "acoes", "passos": list(passos)}


def nao_sei(*palavras):
    return {"tipo": "nao_sei", "palavra": list(palavras)}


def definicao(palavra, *passos, exemplo=None):
    d = {"tipo": "definicao", "palavra": palavra, "passos": list(passos)}
    if exemplo:
        d["objeto_exemplo"] = exemplo
    return d


def cuidado(objeto, **campos):
    return {"tipo": "cuidado", "objeto": objeto, **campos}


def tipo(_tipo, **campos):
    return {"tipo": _tipo, **campos}


ENSINADOS = {
    "quebrar": {"resumo": "(ex.: quebrar ovo) = golpear ovo tigela, abrir ovo tigela, colocar ovo lixo"},
    "bater": {"resumo": "(ex.: bater ovo) = mexer garfo tigela rapido"},
    "fazer bolo": {"resumo": "tarefa ensinada pelo jogador (27 passos)"},
}
PERGUNTA = "Não sei o que é {}. Me explica?"


def caso(fala, categoria, *aceitas, literal=(), ensinados=None, pergunta=None, gravando=None):
    return {"fala": fala, "categoria": categoria, "aceitas": list(aceitas), "literal": list(literal),
            "ensinados": ensinados or {}, "pergunta": pergunta, "gravando": gravando}


FRASES = [
    # ---------------------------------------------------------- comandos com verbos do corpo
    caso("pega o ovo", "comando", acoes(P("pegar", objeto="ovo"))),
    caso("pegue a tigela", "comando", acoes(P("pegar", objeto="tigela"))),
    caso("agarra o garfo", "comando", acoes(P("pegar", objeto="garfo"))),
    caso("pega a faca", "comando", acoes(P("pegar", objeto="faca", parte=None))),
    caso("pega a faca pelo cabo", "comando", acoes(P("pegar", objeto="faca", parte="cabo"))),
    caso("solta isso", "comando", acoes(P("soltar"))),
    caso("larga o garfo", "comando", acoes(P("soltar"))),
    caso("coloca o ovo na tigela", "comando", acoes(P("colocar", objeto="ovo", destino="tigela"))),
    caso("bota a forma no forno", "comando", acoes(P("colocar", objeto="forma", destino="forno"))),
    caso("põe a manteiga na tigela", "comando", acoes(P("colocar", objeto="manteiga", destino="tigela"))),
    caso("joga a casca do ovo no lixo", "comando", acoes(P("colocar", destino="lixo"))),
    caso("despeja duas xícaras de farinha na tigela", "comando",
         acoes(P("despejar", objeto="farinha", destino="tigela", quantidade=2))),
    caso("coloca uma xícara de açúcar na tigela", "comando",
         acoes(P("despejar", objeto="acucar", destino="tigela", quantidade=1)),
         literal=[acoes(P("colocar", objeto="acucar", destino="tigela"))]),
    caso("vira o leite na tigela", "comando",
         acoes(P("despejar", objeto="leite", destino="tigela", quantidade=None))),
    caso("põe uma colher de fermento na tigela", "comando",
         acoes(P("despejar", objeto="fermento", destino="tigela", quantidade=1)),
         literal=[acoes(P("colocar", objeto="fermento", destino="tigela"))]),
    caso("bate o ovo na borda da tigela", "comando", acoes(P("golpear", objeto="ovo", destino="tigela"))),
    caso("abre o ovo em cima da tigela", "comando", acoes(P("abrir", objeto="ovo", destino="tigela"))),
    caso("abre o forno", "comando", acoes(P("abrir", objeto="forno"))),
    caso("fecha a porta do forno", "comando", acoes(P("fechar", objeto="forno"))),
    caso("liga o forno", "comando", acoes(P("ligar", objeto="forno", temperatura=None))),
    caso("liga o forno a 180 graus", "comando", acoes(P("ligar", objeto="forno", temperatura=180))),
    caso("desliga o forno", "comando", acoes(P("desligar"))),
    caso("mexe a tigela devagar", "comando", acoes(P("mexer", destino="tigela", velocidade="devagar"))),
    caso("mexe a massa com a colher", "comando", acoes(P("mexer", objeto="colher"))),
    caso("espera quarenta minutos", "comando", acoes(P("esperar", minutos=40))),
    caso("espera meia hora", "comando", acoes(P("esperar", minutos=30))),
    caso("põe a luva", "comando", acoes(P("vestir"))),
    caso("tira a luva", "comando", acoes(P("tirar"))),
    caso("pega a forma de dentro do forno", "comando", acoes(P("pegar", objeto="forma"))),

    # ---------------------------------------------------------- várias ações numa frase
    caso("pega o garfo e mexe rápido a tigela", "varias",
         acoes(P("pegar", objeto="garfo"), P("mexer", destino="tigela", velocidade="rapido")),
         acoes(P("mexer", objeto="garfo", destino="tigela", velocidade="rapido"))),
    caso("abre o forno, coloca a forma lá dentro e fecha", "varias",
         acoes(P("abrir", objeto="forno"), P("colocar", objeto="forma", destino="forno"), P("fechar"))),
    caso("pega o pacote de farinha, despeja duas xícaras na tigela e solta o pacote", "varias",
         acoes(P("pegar", objeto="farinha"), P("despejar", destino="tigela", quantidade=2), P("soltar"))),
    caso("liga o forno em 180 e espera dez minutos", "varias",
         acoes(P("ligar", objeto="forno", temperatura=180), P("esperar", minutos=10))),
    caso("pega um ovo, bate ele na tigela e abre em cima dela", "varias",
         acoes(P("pegar", objeto="ovo"), P("golpear", destino="tigela"), P("abrir", destino="tigela"))),
    caso("veste a luva e tira a forma do forno", "varias",
         acoes(P("vestir"), P("pegar", objeto="forma"))),

    # ---------------------------------------------------------- verbo que ele não conhece
    caso("bate os ovos", "nao_sei", nao_sei("bater"),
         literal=[acoes(P("golpear", objeto="ovo"))]),
    caso("unta a forma com manteiga", "nao_sei", nao_sei("untar")),
    caso("quebra o ovo", "nao_sei", nao_sei("quebrar")),
    caso("asse o bolo", "nao_sei", nao_sei("assar")),
    caso("liga o liquidificador", "nao_sei", nao_sei("liquidificador")),
    caso("corta a manteiga em pedacinhos", "nao_sei", nao_sei("cortar")),
    caso("derrete a manteiga", "nao_sei", nao_sei("derreter")),
    caso("rala o chocolate", "nao_sei", nao_sei("ralar", "chocolate")),
    caso("tempera a massa", "nao_sei", nao_sei("temperar")),

    # ---------------------------------------------------------- jogador explicando uma palavra
    caso("é pegar o garfo e mexer rápido na tigela", "definicao",
         definicao("bater", P("pegar", objeto="garfo"), P("mexer", destino="tigela", velocidade="rapido")),
         definicao("bater", P("mexer", objeto="garfo", destino="tigela", velocidade="rapido")),
         pergunta=PERGUNTA.format("bater")),
    caso("bater os ovos é mexer eles bem rápido na tigela com o garfo", "definicao",
         definicao("bater", P("pegar", objeto="garfo"), P("mexer", destino="tigela", velocidade="rapido")),
         definicao("bater", P("mexer", objeto="garfo", destino="tigela", velocidade="rapido"))),
    caso("quebrar o ovo é bater ele na borda da tigela, abrir em cima dela e jogar a casca no lixo",
         "definicao",
         definicao("quebrar", P("golpear", destino="tigela"), P("abrir", destino="tigela"),
                   P("colocar", destino="lixo"))),
    caso("assar é abrir o forno, colocar a forma dentro, fechar e esperar quarenta minutos", "definicao",
         definicao("assar", P("abrir", objeto="forno"), P("colocar", objeto="forma", destino="forno"),
                   P("fechar"), P("esperar", minutos=40)),
         pergunta=PERGUNTA.format("assar")),
    caso("untar a forma é colocar manteiga na forma", "definicao",
         definicao("untar", P("colocar", objeto="manteiga", destino="forma"))),
    caso("é ligar o forno em 180 e esperar dez minutos", "definicao",
         definicao("preaquecer", P("ligar", objeto="forno", temperatura=180), P("esperar", minutos=10)),
         pergunta=PERGUNTA.format("preaquecer")),

    # ---------------------------------------------------------- usando o que já foi ensinado
    caso("bate os ovos", "ensinado", acoes(P("bater")), ensinados=ENSINADOS),
    caso("quebra um ovo", "ensinado", acoes(P("quebrar")), ensinados=ENSINADOS),
    caso("quebra três ovos", "ensinado",
         acoes(P("quebrar", quantidade=3)),
         acoes(P("quebrar"), P("quebrar"), P("quebrar")), ensinados=ENSINADOS),
    caso("bate a manteiga", "ensinado", acoes(P("bater", objeto="manteiga")), ensinados=ENSINADOS),
    caso("faz o bolo", "ensinado", acoes(P("fazer bolo")), ensinados=ENSINADOS),
    caso("agora faz um bolo sozinho", "ensinado", acoes(P("fazer bolo")), ensinados=ENSINADOS),
    caso("bate o ovo na borda da tigela", "ensinado",
         acoes(P("golpear", objeto="ovo", destino="tigela")), ensinados=ENSINADOS),
    caso("quebra o ovo e depois bate", "ensinado",
         acoes(P("quebrar"), P("bater")), ensinados=ENSINADOS),

    # ---------------------------------------------------------- tarefas inteiras
    caso("vou te ensinar a fazer um bolo", "tarefa", tipo("comecar_tarefa", nome="bolo")),
    caso("presta atenção, agora você vai aprender a fazer bolo de chocolate", "tarefa",
         tipo("comecar_tarefa", nome="bolo")),
    caso("pronto, isso é fazer bolo", "tarefa", tipo("terminar_tarefa"), gravando="fazer bolo"),
    caso("acabou, é só isso", "tarefa", tipo("terminar_tarefa"), gravando="fazer bolo"),
    caso("terminou a receita", "tarefa", tipo("terminar_tarefa"), gravando="fazer bolo"),

    # ---------------------------------------------------------- cuidados
    caso("a faca você sempre pega pelo cabo", "cuidado", cuidado("faca", parte="cabo")),
    caso("o forno é sempre em 180 graus", "cuidado", cuidado("forno", temperatura=180)),
    caso("sempre que for mexer no forno usa a luva", "cuidado", cuidado("forno", luva=True)),
    caso("nunca pega a faca pela lâmina", "cuidado", cuidado("faca", parte="cabo")),
    caso("cuidado, a forma sai quente do forno, pega com luva", "cuidado",
         cuidado("forma", luva=True), cuidado("forno", luva=True)),

    # ---------------------------------------------------------- conversa e parar
    caso("muito bem, robozinho!", "conversa", tipo("conversa")),
    caso("você é muito burro", "conversa", tipo("conversa")),
    caso("para, para, para!", "conversa", tipo("parar")),
    caso("o que você tá fazendo?", "conversa", tipo("conversa")),
    caso("não, para com isso", "conversa", tipo("parar")),
]


def linha(fala, esperado, depois=None):
    d = {"fala": fala, "esperado": esperado}
    if depois:
        d["depois"] = depois
    return d


ROTEIROS = [
    {
        "nome": "didatica",
        "descricao": "explica tudo, com quantidade, temperatura e luva",
        "ensino": [
            linha("vou te ensinar a fazer um bolo", tipo("comecar_tarefa", nome="fazer bolo")),
            linha("liga o forno em 180 graus", acoes(P("ligar", objeto="forno", temperatura=180))),
            linha("pega o pacote de farinha e despeja duas xícaras na tigela",
                  acoes(P("pegar", objeto="farinha"), P("despejar", destino="tigela", quantidade=2))),
            linha("solta o pacote", acoes(P("soltar"))),
            linha("despeja uma xícara de açúcar na tigela",
                  acoes(P("despejar", objeto="acucar", destino="tigela", quantidade=1))),
            linha("solta o açúcar", acoes(P("soltar"))),
            linha("quebra um ovo", nao_sei("quebrar"), depois=acoes(P("quebrar", objeto="ovo"))),
            linha("quebrar é bater o ovo na borda da tigela, abrir ele em cima da tigela e jogar a casca no lixo",
                  definicao("quebrar", P("golpear", objeto="ovo", destino="tigela"),
                            P("abrir", objeto="ovo", destino="tigela"),
                            P("colocar", objeto="ovo", destino="lixo"), exemplo="ovo")),
            linha("quebra mais dois ovos", acoes(P("quebrar", objeto="ovo", quantidade=2))),
            linha("despeja uma xícara de leite na tigela",
                  acoes(P("despejar", objeto="leite", destino="tigela", quantidade=1))),
            linha("solta o leite", acoes(P("soltar"))),
            linha("põe a manteiga na tigela", acoes(P("colocar", objeto="manteiga", destino="tigela"))),
            linha("despeja uma colher de fermento na tigela",
                  acoes(P("despejar", objeto="fermento", destino="tigela", quantidade=1))),
            linha("solta o fermento", acoes(P("soltar"))),
            linha("agora bate a massa", nao_sei("bater"), depois=acoes(P("bater"))),
            linha("bater é pegar o garfo e mexer a tigela bem rápido",
                  definicao("bater", P("pegar", objeto="garfo"),
                            P("mexer", destino="tigela", velocidade="rapido"))),
            linha("solta o garfo", acoes(P("soltar"))),
            linha("despeja a massa da tigela na forma", acoes(P("despejar", objeto="tigela", destino="forma"))),
            linha("solta a tigela", acoes(P("soltar"))),
            linha("veste a luva", acoes(P("vestir", objeto="luva"))),
            linha("abre o forno e coloca a forma lá dentro",
                  acoes(P("abrir", objeto="forno"), P("colocar", objeto="forma", destino="forno"))),
            linha("fecha o forno", acoes(P("fechar", objeto="forno"))),
            linha("espera quarenta minutos", acoes(P("esperar", minutos=40))),
            linha("abre o forno e tira a forma", acoes(P("abrir", objeto="forno"), P("pegar", objeto="forma"))),
            linha("coloca a forma na mesa", acoes(P("colocar", objeto="forma", destino="mesa"))),
            linha("desliga o forno", acoes(P("desligar", objeto="forno"))),
            linha("tira a luva", acoes(P("tirar", objeto="luva"))),
            linha("pronto, isso é fazer bolo", tipo("terminar_tarefa")),
        ],
        "provas": [
            {"antes": [], "fala": linha("agora faz um bolo sozinho", acoes(P("fazer bolo")))},
        ],
    },
    {
        "nome": "apressada",
        "descricao": "fala pouco, não diz quanto nem a temperatura, esquece a luva; depois corrige",
        "ensino": [
            linha("bora fazer um bolo, presta atenção", tipo("comecar_tarefa", nome="fazer bolo")),
            linha("liga o forno", acoes(P("ligar", objeto="forno"))),
            linha("farinha na tigela", acoes(P("despejar", objeto="farinha", destino="tigela"))),
            linha("solta", acoes(P("soltar"))),
            linha("joga o açúcar na tigela também", acoes(P("despejar", objeto="acucar", destino="tigela"))),
            linha("solta", acoes(P("soltar"))),
            linha("põe três ovos na tigela",
                  acoes(P("colocar", objeto="ovo", destino="tigela"), P("colocar", objeto="ovo", destino="tigela"),
                        P("colocar", objeto="ovo", destino="tigela"))),
            linha("joga o leite também", acoes(P("despejar", objeto="leite", destino="tigela"))),
            linha("solta", acoes(P("soltar"))),
            linha("põe o fermento na tigela", acoes(P("colocar", objeto="fermento", destino="tigela"))),
            linha("mexe com a mão mesmo", acoes(P("mexer"))),
            linha("joga a massa na forma", acoes(P("despejar", objeto="tigela", destino="forma"))),
            linha("solta", acoes(P("soltar"))),
            linha("abre o forno e põe a forma lá dentro",
                  acoes(P("abrir", objeto="forno"), P("colocar", objeto="forma", destino="forno"))),
            linha("fecha", acoes(P("fechar", objeto="forno"))),
            linha("espera uma hora", acoes(P("esperar", minutos=60))),
            linha("tira o bolo do forno", acoes(P("pegar", objeto="forma"))),
            linha("abre o forno, né", acoes(P("abrir", objeto="forno"))),
            linha("tira o bolo", acoes(P("pegar", objeto="forma"))),
            linha("ai, veste a luva e tira o bolo", acoes(P("vestir", objeto="luva"), P("pegar", objeto="forma"))),
            linha("põe na mesa", acoes(P("colocar", destino="mesa"))),
            linha("pronto", tipo("terminar_tarefa")),
        ],
        "provas": [
            {"antes": [], "fala": linha("faz o bolo", acoes(P("fazer bolo")))},
            {"antes": [
                linha("o forno é sempre a 180 graus", cuidado("forno", temperatura=180)),
                linha("e sempre usa luva quando mexer no forno", cuidado("forno", luva=True)),
            ], "fala": linha("faz o bolo de novo", acoes(P("fazer bolo")))},
        ],
    },
    {
        "nome": "generalizacao",
        "descricao": "ensina bater com ovo e depois pede para bater a manteiga",
        "ensino": [
            linha("bater os ovos é mexer eles bem rápido com o garfo na tigela",
                  definicao("bater", P("mexer", objeto="garfo", destino="tigela", velocidade="rapido"),
                            exemplo="ovo")),
            linha("põe a manteiga na tigela", acoes(P("colocar", objeto="manteiga", destino="tigela"))),
            linha("bate a manteiga", acoes(P("bater", objeto="manteiga"))),
        ],
        "provas": [],
        "verificar": "Mexi a tigela rápido com garfo",
    },
]
