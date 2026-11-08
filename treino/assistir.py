"""Mostra um modelo salvo jogando, para gravar o vídeo.

Rode este script e, quando ele disser que está esperando conexão, aperte F5
no Godot (abre a cena de demo, com uma arena só e câmera de perto).
Passando um checkpoint do começo do treino, dá para gravar a versão que ainda
não sabe nada. Ctrl+C para parar.

Uso: python treino/assistir.py treinos/primeiro/modelo.zip
"""
import argparse

from godot_rl.wrappers.stable_baselines_wrapper import StableBaselinesGodotEnv
from stable_baselines3 import PPO


def main() -> None:
    p = argparse.ArgumentParser(description="Mostra um agente treinado jogando.")
    p.add_argument("modelo", help=".zip salvo pelo treinar.py (modelo ou checkpoint)")
    p.add_argument("--jogo", default=None,
                   help="executável exportado do Godot; sem isso, espera o F5 no editor")
    p.add_argument("--sortear", action="store_true",
                   help="sorteia as ações pela política em vez de pegar sempre a mais provável")
    args = p.parse_args()

    env = StableBaselinesGodotEnv(env_path=args.jogo, show_window=True, speedup=1)
    modelo = PPO.load(args.modelo)

    obs = env.reset()
    try:
        while True:
            acao, _ = modelo.predict(obs, deterministic=not args.sortear)
            obs, _, _, _ = env.step(acao)
    except KeyboardInterrupt:
        pass
    finally:
        env.close()


if __name__ == "__main__":
    main()
