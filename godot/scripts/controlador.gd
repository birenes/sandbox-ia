extends AIController3D
## Ligação do agente com o treino: o que ele enxerga, o que ele pode fazer e
## quanto ganhou. A pontuação em si é calculada pela arena (arena.gd).

var arena  # a arena preenche ao iniciar
var movimento := Vector2.ZERO


func get_obs() -> Dictionary:
	return {"obs": arena.observacao()}


func get_reward() -> float:
	return reward


func get_action_space() -> Dictionary:
	return {
		"mover": {"size": 2, "action_type": "continuous"},
	}


func set_action(action) -> void:
	movimento = Vector2(
		clampf(action["mover"][0], -1.0, 1.0),
		clampf(action["mover"][1], -1.0, 1.0)
	)
