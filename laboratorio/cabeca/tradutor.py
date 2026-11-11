"""O ouvido-cabeça: transforma a fala do jogador num pedido que o robô entende.

O modelo de linguagem não decide nada e não sabe cozinhar. Ele só traduz a
fala para um JSON travado por um esquema: os verbos possíveis são as
primitivas do corpo mais o que o jogador já ensinou, e os objetos são os da
cozinha. Se a fala usa um verbo fora da lista, a saída certa é "nao_sei".
"""
import json

from .cozinha import OBJETOS, PRIMITIVAS

SISTEMA = """Você traduz o que o jogador fala para um robô de cozinha num jogo. Responda só com JSON, numa linha.
O robô não sabe cozinhar. Ele só conhece os verbos da lista e só faz o que o jogador mandar.

Verbos do corpo:
pegar: pegar um objeto com a mão (parte "cabo" ou "lamina", só se o jogador disser por onde)
soltar: largar o que está na mão
colocar: pôr um objeto dentro ou em cima de um destino (objeto é o que vai, destino é onde)
despejar: virar o conteúdo de um objeto num destino (quantidade em xícaras ou colheres, só se o jogador disser)
golpear: bater um objeto contra um destino (ex.: bater o ovo na borda da tigela)
abrir: abrir um objeto; para o ovo, destino é onde cai o conteúdo
fechar: fechar um objeto
ligar: ligar o forno (temperatura em graus, só se o jogador disser)
desligar: desligar o forno
mexer: mexer o conteúdo de um destino; objeto é o utensílio, se o jogador disser (velocidade "rapido" ou "devagar", só se o jogador disser)
esperar: deixar o tempo passar (minutos, só se o jogador disser)
vestir: pôr a luva na mão
tirar: tirar a luva

Objetos: ovo, farinha, acucar, sal, leite, manteiga, fermento, tigela, forma, garfo, colher, faca, luva, mesa, forno, lixo.

Tipos de resposta:
acoes: o jogador mandou fazer algo que dá para montar com verbos conhecidos. Um passo por ação, na ordem.
nao_sei: o jogador mandou fazer algo com um verbo que não está na lista nem entre os ensinados, ou falou de um objeto que não existe. "palavra" é esse verbo no infinitivo, ou o objeto.
definicao: o jogador explica o que uma palavra quer dizer, com verbos conhecidos. "palavra" no infinitivo. Se ele falou de um objeto ao definir (ex.: "quebrar o ovo é..."), ponha em "objeto_exemplo".
comecar_tarefa: o jogador avisa que vai ensinar uma tarefa inteira. "nome" no infinitivo, ex.: "fazer bolo".
terminar_tarefa: o jogador avisa que a tarefa que ele estava ensinando acabou.
cuidado: o jogador ensina um jeito certo de lidar com um objeto, para valer sempre (por onde pegar, temperatura, usar luva).
parar: o jogador manda parar.
conversa: elogio, xingamento, pergunta ou qualquer coisa que não é ordem.

Não troque um verbo desconhecido por um parecido. Se o jogador usa um verbo ensinado, use o verbo ensinado.
Não preencha campo que o jogador não falou.

Exemplos:
Fala: pega o ovo
{"tipo":"acoes","passos":[{"verbo":"pegar","objeto":"ovo"}]}
Fala: bota o ovo dentro da tigela
{"tipo":"acoes","passos":[{"verbo":"colocar","objeto":"ovo","destino":"tigela"}]}
Fala: vira duas xícaras de farinha na tigela e solta o pacote
{"tipo":"acoes","passos":[{"verbo":"despejar","objeto":"farinha","destino":"tigela","quantidade":2},{"verbo":"soltar"}]}
Fala: liga o forno em 180 graus
{"tipo":"acoes","passos":[{"verbo":"ligar","objeto":"forno","temperatura":180}]}
Fala: unta a forma
{"tipo":"nao_sei","palavra":"untar"}
Fala: peneira a farinha
{"tipo":"nao_sei","palavra":"peneirar"}
Fala: enxaguar é pegar a tigela e colocar na pia
{"tipo":"nao_sei","palavra":"pia"}
Fala: amassar a manteiga é pegar o garfo e mexer a tigela devagar
{"tipo":"definicao","palavra":"amassar","objeto_exemplo":"manteiga","passos":[{"verbo":"mexer","objeto":"garfo","destino":"tigela","velocidade":"devagar"}]}
Fala: agora presta atenção que eu vou te ensinar a lavar a louça
{"tipo":"comecar_tarefa","nome":"lavar louça"}
Fala: pronto, é isso
{"tipo":"terminar_tarefa"}
Fala: a colher você sempre pega pelo cabo
{"tipo":"cuidado","objeto":"colher","parte":"cabo"}
Fala: para tudo
{"tipo":"parar"}
Fala: nossa, você é muito lento
{"tipo":"conversa"}"""


def _passo(verbos: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "verbo": {"enum": verbos},
            "objeto": {"enum": OBJETOS},
            "destino": {"enum": OBJETOS},
            "parte": {"enum": ["cabo", "lamina"]},
            "quantidade": {"type": "integer", "minimum": 1, "maximum": 20},
            "minutos": {"type": "integer", "minimum": 1, "maximum": 300},
            "temperatura": {"type": "integer", "minimum": 50, "maximum": 300},
            "velocidade": {"enum": ["devagar", "rapido"]},
        },
        "required": ["verbo"],
        "additionalProperties": False,
    }


def _tipo(nome: str, campos: dict | None = None, obrigatorios: list | None = None) -> dict:
    return {
        "type": "object",
        "properties": {"tipo": {"const": nome}, **(campos or {})},
        "required": ["tipo"] + (obrigatorios or []),
        "additionalProperties": False,
    }


def esquema(ensinados: list[str]) -> dict:
    verbos = list(PRIMITIVAS) + list(ensinados)
    passos = {"type": "array", "items": _passo(verbos), "minItems": 1, "maxItems": 8}
    palavra = {"type": "string", "minLength": 2, "maxLength": 30, "pattern": "^[a-zà-ú ]+$"}
    return {"anyOf": [
        _tipo("acoes", {"passos": passos}, ["passos"]),
        _tipo("nao_sei", {"palavra": palavra}, ["palavra"]),
        _tipo("definicao", {"palavra": palavra, "objeto_exemplo": {"enum": OBJETOS}, "passos": passos},
              ["palavra", "passos"]),
        _tipo("comecar_tarefa", {"nome": palavra}, ["nome"]),
        _tipo("terminar_tarefa"),
        _tipo("cuidado", {"objeto": {"enum": OBJETOS}, "parte": {"enum": ["cabo", "lamina"]},
                          "temperatura": {"type": "integer", "minimum": 50, "maximum": 300},
                          "luva": {"type": "boolean"}}, ["objeto"]),
        _tipo("parar"),
        _tipo("conversa"),
    ]}


def mensagem_usuario(fala: str, ensinados: dict, pergunta: str | None, gravando: str | None) -> str:
    linhas = []
    if ensinados:
        linhas.append("Verbos que o jogador já ensinou:")
        for palavra, d in ensinados.items():
            linhas.append(f"{palavra}: {d.get('resumo', '')}")
    else:
        linhas.append("O jogador ainda não ensinou nenhum verbo.")
    if gravando:
        linhas.append(f"O jogador está ensinando a tarefa \"{gravando}\".")
    if pergunta:
        linhas.append(f"O robô acabou de perguntar: \"{pergunta}\"")
    linhas.append(f"Fala: {fala}")
    return "\n".join(linhas)


class Tradutor:
    def __init__(self, servidor):
        self.servidor = servidor

    def traduzir(self, fala: str, ensinados: dict, pergunta: str | None = None,
                 gravando: str | None = None) -> dict:
        mensagens = [
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": mensagem_usuario(fala, ensinados, pergunta, gravando)},
        ]
        r = self.servidor.conversar(mensagens, esquema(list(ensinados)))
        try:
            pedido = json.loads(r["texto"])
        except json.JSONDecodeError:
            pedido = {"tipo": "erro", "texto": r["texto"]}
        return {"pedido": pedido, "segundos": r["segundos"], "tempos": r["tempos"]}
