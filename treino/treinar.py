"""Treina o agente com PPO (Stable-Baselines3) na cena de treino do Godot.

Dois jeitos de rodar:
  1. Pelo editor: rode este script e, quando ele disser que está esperando
     conexão, abra cenas/treino.tscn no Godot e aperte F6.
  2. Pelo jogo exportado: passe --jogo com o caminho do executável.

O agente mestre (mestre.py) acompanha todos os episódios e escreve o diário de
bordo em treinos/<nome>/diario.md, guardando os episódios que fugiram do normal
para filmar depois. Os checkpoints do modelo também ficam salvos.

Uso: python treino/treinar.py --passos 300000 --nome primeiro
"""
import argparse
from datetime import datetime
from pathlib import Path

from godot_rl.wrappers.stable_baselines_wrapper import StableBaselinesGodotEnv
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.vec_env.vec_monitor import VecMonitor

from mestre import criar_callback

RAIZ = Path(__file__).resolve().parent.parent


def main() -> None:
    p = argparse.ArgumentParser(description="Treina o agente do sandbox-ia.")
    p.add_argument("--jogo", default=None,
                   help="executável exportado do Godot; sem isso, espera o F6 no editor")
    p.add_argument("--passos", type=int, default=300_000, help="total de passos de treino")
    p.add_argument("--nome", default=None, help="nome do experimento (padrão: data e hora)")
    p.add_argument("--janela", action="store_true",
                   help="mostra a janela do jogo durante o treino (só com --jogo)")
    p.add_argument("--acelerar", type=int, default=8,
                   help="velocidade do jogo durante o treino (só com --jogo)")
    p.add_argument("--checkpoint_a_cada", type=int, default=25_000,
                   help="de quantos em quantos passos salvar um checkpoint")
    p.add_argument("--continuar", default=None, help=".zip de um treino anterior")
    args = p.parse_args()

    nome = args.nome or datetime.now().strftime("%Y-%m-%d_%H%M")
    pasta = RAIZ / "treinos" / nome
    pasta.mkdir(parents=True, exist_ok=True)

    env = StableBaselinesGodotEnv(
        env_path=args.jogo,
        show_window=args.janela,
        seed=0,
        n_parallel=1,
        speedup=args.acelerar,
    )
    env = VecMonitor(env)

    if args.continuar:
        modelo = PPO.load(args.continuar, env=env, tensorboard_log=str(pasta))
    else:
        modelo = PPO(
            "MultiInputPolicy",
            env,
            n_steps=256,
            batch_size=256,
            verbose=1,
            tensorboard_log=str(pasta),
        )

    checkpoints = CheckpointCallback(
        save_freq=max(args.checkpoint_a_cada // env.num_envs, 1),
        save_path=str(pasta / "checkpoints"),
        name_prefix="agente",
    )

    mestre = criar_callback(pasta)

    try:
        modelo.learn(total_timesteps=args.passos, callback=[checkpoints, mestre], tb_log_name="ppo")
    finally:
        modelo.save(pasta / "modelo.zip")
        env.close()
        print(f"Modelo salvo em {pasta / 'modelo.zip'}")
        print(f"Diário de bordo em {pasta / 'diario.md'} ({mestre.mestre.marcados} episódios marcados)")


if __name__ == "__main__":
    main()
