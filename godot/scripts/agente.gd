extends CharacterBody3D
## Corpo do agente. Anda pelo chão da arena, pelas setas do teclado ou pelas
## ações que chegam do treino em Python.

@export var velocidade_max := 6.0
@export var aceleracao := 40.0

var arena  # a arena preenche ao iniciar
var gravidade: float = ProjectSettings.get_setting("physics/3d/default_gravity")

@onready var controlador = $Controlador


func _ready() -> void:
	controlador.init(self)


func _physics_process(delta: float) -> void:
	if controlador.needs_reset:
		if controlador.n_steps > controlador.reset_after:
			controlador.done = true  # acabou o tempo do episódio sem chegar no alvo
		controlador.reset()
		arena.reiniciar()
		return

	var comando: Vector2
	if controlador.heuristic == "human":
		comando = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
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

	arena.depois_do_passo()
