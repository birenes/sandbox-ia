extends Node
## Gravador da arena: anota cada episódio (trajetória e eventos) para o mestre
## analisar e para o replay reproduzir depois. Grava estado, não imagem, então
## ocupa pouco espaço e o vídeo pode ser filmado depois com qualquer câmera.
##
## Durante o treino, os episódios prontos vão para o Python junto com cada passo
## (ver controlador.gd). Com --gravar_em=<pasta> na linha de comando, também
## ficam salvos em <pasta>/episodios.jsonl, mesmo sem treino rodando.

const Argumentos = preload("res://scripts/argumentos.gd")
const MAXIMO_ESPERANDO := 50  # sem ninguém buscando, não acumula para sempre

@export var a_cada := 4  # anota a posição a cada tantos quadros de física

var numero := 0
var gravando := false
var quadro := 0
var episodio := {}
var prontos: Array = []
var _arquivo_saida := ""


func _ready() -> void:
	var pasta := Argumentos.valor("gravar_em")
	if pasta != "":
		DirAccess.make_dir_recursive_absolute(pasta)
		_arquivo_saida = pasta.path_join("episodios.jsonl")


func comecar(agente_pos: Vector3, alvo_pos: Vector3) -> void:
	numero += 1
	quadro = 0
	gravando = true
	episodio = {
		"arena": String(get_parent().name),
		"numero": numero,
		"inicio": {"agente": vetor(agente_pos), "alvo": vetor(alvo_pos)},
		"a_cada": a_cada,
		"trajetoria": [],
		"eventos": [],
	}


func passo(agente: Node3D) -> void:
	if not gravando:
		return
	if quadro % a_cada == 0:
		var p := agente.position
		episodio["trajetoria"].append([
			snappedf(p.x, 0.01), snappedf(p.y, 0.01), snappedf(p.z, 0.01),
			snappedf(agente.rotation.y, 0.01),
		])
	quadro += 1


func evento(tipo: String, dados: Dictionary = {}) -> void:
	if not gravando:
		return
	var registro := {"quadro": quadro, "tipo": tipo}
	registro.merge(dados)
	episodio["eventos"].append(registro)


func terminar(resultado: String, pontos: float) -> void:
	if not gravando:
		return
	gravando = false
	var quadros_por_segundo := Engine.physics_ticks_per_second / Engine.time_scale
	episodio["resultado"] = resultado
	episodio["quadros"] = quadro
	episodio["duracao_s"] = snappedf(quadro / quadros_por_segundo, 0.01)
	episodio["pontos"] = snappedf(pontos, 0.001)
	prontos.append(episodio)
	if prontos.size() > MAXIMO_ESPERANDO:
		prontos.pop_front()
	if _arquivo_saida != "":
		_salvar(episodio)


## Entrega os episódios terminados e esvazia a fila.
func retirar_prontos() -> Array:
	var lista := prontos
	prontos = []
	return lista


func vetor(v: Vector3) -> Array:
	return [snappedf(v.x, 0.01), snappedf(v.y, 0.01), snappedf(v.z, 0.01)]


func _salvar(ep: Dictionary) -> void:
	var arquivo: FileAccess
	if FileAccess.file_exists(_arquivo_saida):
		arquivo = FileAccess.open(_arquivo_saida, FileAccess.READ_WRITE)
		if arquivo != null:
			arquivo.seek_end()
	else:
		arquivo = FileAccess.open(_arquivo_saida, FileAccess.WRITE)
	if arquivo == null:
		push_warning("Não consegui gravar em %s" % _arquivo_saida)
		return
	arquivo.store_line(JSON.stringify(ep))
	arquivo.close()
