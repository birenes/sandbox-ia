extends Node3D
## Reproduz um episódio gravado, com uma câmera que acompanha o agente.
##
## Pelo editor: escolha o arquivo em "arquivo_episodio" no inspetor e aperte F6.
## Pela linha de comando (é o que o treino/filmar.py faz):
##   godot --path godot res://cenas/replay.tscn -- --episodio=C:/caminho/000123.json --sair_no_fim

const Argumentos = preload("res://scripts/argumentos.gd")
const RESULTADOS := {
	"acertou": "chegou no alvo",
	"tempo_esgotado": "tempo esgotado",
	"saiu_da_arena": "saiu da arena",
	"interrompido": "interrompido",
}

@export_global_file("*.json") var arquivo_episodio := ""
@export var mostrar_legenda := true
@export var distancia_camera := Vector3(0, 7, 9)
@export var suavidade_camera := 0.08
@export var quadros_parado_no_fim := 60

@onready var arena = $Arena
@onready var camera: Camera3D = $Camera
@onready var legenda: Label = $Tela/Legenda

var episodio := {}
var trajetoria: Array = []
var a_cada := 4
var quadro := 0
var total_quadros := 0
var sair_no_fim := false


func _ready() -> void:
	arena.em_replay = true
	sair_no_fim = Argumentos.tem("sair_no_fim")
	var caminho := Argumentos.valor("episodio", arquivo_episodio)
	if not _carregar(caminho):
		set_physics_process(false)
		if sair_no_fim:
			get_tree().quit(1)
		return
	legenda.visible = mostrar_legenda
	legenda.text = _texto_legenda()
	_posicionar(0.0)
	camera.position = _lugar_da_camera()
	camera.look_at(_ponto_de_mira())


func _physics_process(_delta: float) -> void:
	if quadro <= total_quadros:
		_posicionar(float(quadro) / a_cada)
	quadro += 1
	camera.position = camera.position.lerp(_lugar_da_camera(), suavidade_camera)
	camera.look_at(_ponto_de_mira())
	if quadro > total_quadros + quadros_parado_no_fim:
		if sair_no_fim:
			get_tree().quit()
		else:
			quadro = 0  # no editor, repete


func _carregar(caminho: String) -> bool:
	if caminho == "":
		legenda.text = "Nenhum episódio escolhido. Preencha arquivo_episodio no inspetor."
		push_warning(legenda.text)
		return false
	var dados = JSON.parse_string(FileAccess.get_file_as_string(caminho))
	if typeof(dados) != TYPE_DICTIONARY or not dados.has("trajetoria") or dados["trajetoria"].is_empty():
		legenda.text = "Não consegui ler o episódio em %s" % caminho
		push_error(legenda.text)
		return false
	episodio = dados
	trajetoria = episodio["trajetoria"]
	a_cada = int(episodio.get("a_cada", 4))
	total_quadros = (trajetoria.size() - 1) * a_cada
	var alvo: Array = episodio["inicio"]["alvo"]
	arena.alvo.position = Vector3(alvo[0], alvo[1], alvo[2])
	return true


func _posicionar(indice: float) -> void:
	var i := clampi(int(floorf(indice)), 0, trajetoria.size() - 1)
	var j := mini(i + 1, trajetoria.size() - 1)
	var t := indice - floorf(indice)
	var a: Array = trajetoria[i]
	var b: Array = trajetoria[j]
	arena.agente.position = Vector3(lerpf(a[0], b[0], t), lerpf(a[1], b[1], t), lerpf(a[2], b[2], t))
	arena.agente.rotation.y = lerp_angle(a[3], b[3], t)


func _lugar_da_camera() -> Vector3:
	return arena.agente.position + distancia_camera


func _ponto_de_mira() -> Vector3:
	return arena.agente.position + Vector3(0, 0.5, 0)


func _texto_legenda() -> String:
	var linhas := PackedStringArray()
	linhas.append("%s, episódio %d" % [episodio.get("arena", "?"), int(episodio.get("numero", 0))])
	if episodio.has("passo_treino"):
		linhas.append("passo de treino %d" % int(episodio["passo_treino"]))
	var resultado: String = RESULTADOS.get(episodio.get("resultado", ""), "")
	var segundos := ("%.1f" % float(episodio.get("duracao_s", 0.0))).replace(".", ",")
	linhas.append("%s em %s s" % [resultado, segundos])
	for motivo in episodio.get("motivos", []):
		linhas.append(str(motivo))
	return "\n".join(linhas)
