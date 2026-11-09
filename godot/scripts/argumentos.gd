extends RefCounted
## Lê os argumentos passados depois de "--" na linha de comando,
## no formato --nome=valor ou só --nome (que vale "true").


static func valor(nome: String, padrao: String = "") -> String:
	for arg in OS.get_cmdline_user_args():
		var limpo := arg.trim_prefix("--")
		if limpo == nome:
			return "true"
		if limpo.begins_with(nome + "="):
			return limpo.substr(nome.length() + 1)
	return padrao


static func tem(nome: String) -> bool:
	return valor(nome) != ""
