extends CharacterBody3D
## Corpo do agente. Anda pelo chão da arena, pelas setas do teclado ou pelas
## ações que chegam do treino em Python.
## Com --piloto na linha de comando, quem dirige é um piloto automático
## simples (vai no rumo do alvo, errando um pouco). Serve de comparação com a
## IA e para testar o gravador sem treino.

const Argumentos = preload("res://scripts/argumentos.gd")

@export var velocidade_max := 6.0
@export var aceleracao := 40.0

var arena  # a arena preenche ao iniciar
var gravidade: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var piloto := false
var _desvio := Vector2.ZERO
var _encostado_na_parede := false

@onready var controlador = $Controlador


func _ready() -> void:
	controlador.init(self)
	piloto = Argumentos.tem("piloto")


func _physics_process(delta: float) -> void:
	if arena == null or arena.em_replay:
		return

	if controlador.needs_reset:
		if controlador.n_steps > controlador.reset_after:
			arena.fim_de_episodio("tempo_esgotado")
		controlador.reset()
		arena.reiniciar()
		return

	var comando: Vector2
	if controlador.heuristic == "human":
		comando = _piloto_automatico() if piloto else Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	else:
		comando = controlador.movimento
	comando = comando.limit_length(1.0)

	velocity.x = move_toward(velocity.x, comando.x * velocidade_max, aceleracao * delta)
	velocity.z = move_toward(velocity.z, comando.y * velocidade_max, aceleracao * delta)
	if not is_on_floor():
		velocity.y -= gravidade * delta
	move_and_slide()

	if Vector2(velocity.x, velocity.z).length() > 0.5:
		rotation.y = atan2(-velocity.x, -velocity.z)  # vira pra onde está andando

	if is_on_wall() and not _encostado_na_parede:
		arena.gravador.evento("bateu_na_parede")
	_encostado_na_parede = is_on_wall()

	arena.depois_do_passo()


func _piloto_automatico() -> Vector2:
	# o desvio muda aos poucos, então às vezes ele se perde e às vezes acerta de primeira
	_desvio = (_desvio + Vector2(randf_range(-0.2, 0.2), randf_range(-0.2, 0.2))).limit_length(2.0)
	return (arena.direcao_ao_alvo() + _desvio).limit_length(1.0)
