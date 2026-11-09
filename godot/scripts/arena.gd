extends Node3D
## Uma arena: chão, quatro paredes, o agente e o alvo.
## Aqui ficam as regras do jogo: onde cada um nasce, o que o agente enxerga e
## quanto ele ganha ou perde a cada passo. O gravador anota tudo.

const TAMANHO := 20.0          # lado do chão, em metros
const MARGEM := 1.5            # distância mínima das paredes ao sortear posições
const RAIO_ALVO := 1.2         # mais perto que isso, conta como chegou
const DISTANCIA_MINIMA := 5.0  # o alvo nunca nasce colado no agente

@onready var agente = $Agente
@onready var controlador = $Agente/Controlador
@onready var alvo: Node3D = $Alvo
@onready var gravador = $Gravador

var distancia_anterior := 0.0
var pontos_episodio := 0.0
var acertos := 0
var em_replay := false  # no replay, quem move o agente é a gravação


func _ready() -> void:
	agente.arena = self
	controlador.arena = self
	reiniciar()


func reiniciar() -> void:
	if gravador.gravando:
		gravador.terminar("interrompido", pontos_episodio)
	var limite := TAMANHO / 2.0 - MARGEM
	agente.position = Vector3(randf_range(-limite, limite), 1.0, randf_range(-limite, limite))
	agente.velocity = Vector3.ZERO
	var posicao := Vector3.ZERO
	for _tentativa in 100:
		posicao = Vector3(randf_range(-limite, limite), 0.6, randf_range(-limite, limite))
		if _no_chao(posicao).distance_to(_no_chao(agente.position)) >= DISTANCIA_MINIMA:
			break
	alvo.position = posicao
	distancia_anterior = _distancia()
	pontos_episodio = 0.0
	gravador.comecar(agente.position, alvo.position)


## Chamado pelo agente depois de cada movimento.
func depois_do_passo() -> void:
	gravador.passo(agente)
	var distancia := _distancia()
	_pontuar((distancia_anterior - distancia) * 0.1)  # chegou mais perto, ganha um pouco
	_pontuar(-0.001)  # cada instante custa, pra ele não ficar enrolando
	distancia_anterior = distancia
	if _fora_da_arena():
		gravador.evento("saiu_da_arena", {"posicao": gravador.vetor(agente.position)})
		fim_de_episodio("saiu_da_arena")
	elif distancia < RAIO_ALVO:
		acertos += 1
		_pontuar(1.0)
		fim_de_episodio("acertou")


func fim_de_episodio(resultado: String) -> void:
	gravador.terminar(resultado, pontos_episodio)
	controlador.done = true
	controlador.needs_reset = true


## O que o agente enxerga: 6 números, todos mais ou menos entre -1 e 1.
func observacao() -> Array:
	var ate_o_alvo: Vector2 = _no_chao(alvo.position - agente.position) / TAMANHO
	var onde_estou: Vector2 = _no_chao(agente.position) / (TAMANHO / 2.0)
	var velocidade: Vector2 = _no_chao(agente.velocity) / agente.velocidade_max
	return [ate_o_alvo.x, ate_o_alvo.y, onde_estou.x, onde_estou.y, velocidade.x, velocidade.y]


func direcao_ao_alvo() -> Vector2:
	return _no_chao(alvo.position - agente.position).normalized()


func _pontuar(valor: float) -> void:
	controlador.reward += valor
	pontos_episodio += valor


func _fora_da_arena() -> bool:
	var p: Vector3 = agente.position
	var limite := TAMANHO / 2.0 + 1.0
	return absf(p.x) > limite or absf(p.z) > limite or p.y < -2.0


func _distancia() -> float:
	return _no_chao(alvo.position).distance_to(_no_chao(agente.position))


func _no_chao(v: Vector3) -> Vector2:
	return Vector2(v.x, v.z)
