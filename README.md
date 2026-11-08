# sandbox-ia

Laboratório em Godot para treinar agentes com aprendizado por reforço e gravar o
processo em vídeo. Cada ambiente novo é um desafio diferente, e os checkpoints do
treino permitem mostrar o agente errando no começo e acertando no fim.

Estado atual: primeira versão, com um ambiente (alcançar o alvo).

## O que tem aqui

```
godot/                  projeto Godot 4
  cenas/arena.tscn      uma arena: chão, paredes, agente e alvo
  cenas/treino.tscn     16 arenas lado a lado para treinar em paralelo
  cenas/demo.tscn       uma arena com câmera de perto, para testar e gravar
  scripts/arena.gd      regras do jogo: onde cada um nasce, o que o agente vê, pontuação
  scripts/agente.gd     corpo do agente (movimento)
  scripts/controlador.gd  ligação com o treino (observação, ações, recompensa)
treino/
  treinar.py            treina com PPO (Stable-Baselines3) e salva checkpoints
  assistir.py           mostra um modelo salvo jogando
scripts/
  instalar_plugin.py    baixa o plugin Godot RL Agents para godot/addons
```

## Como rodar

Precisa de Godot 4 (a versão padrão serve, não precisa da .NET), git e Python 3.10
ou 3.11. O godot-rl declara suporte até a 3.10, então versões muito novas do Python
podem não instalar alguma dependência.

1. Baixar o plugin (ele não fica no repositório):

   ```
   python scripts/instalar_plugin.py
   ```

2. Criar o ambiente Python:

   ```
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install -r treino/requirements.txt
   ```

3. Testar no teclado: abrir `godot/project.godot` no Godot e apertar F5. Sem treino
   rodando, o plugin avisa que não achou o Python e o agente passa a obedecer às setas.

4. Treinar: rodar o script e, quando ele disser que está esperando conexão, abrir
   `cenas/treino.tscn` no Godot e apertar F6.

   ```
   python treino/treinar.py --passos 300000 --nome primeiro
   ```

   O resultado fica em `treinos/primeiro/` (modelo final, checkpoints e log).

5. Acompanhar o aprendizado:

   ```
   tensorboard --logdir treinos
   ```

6. Assistir: rodar o script com um modelo salvo e apertar F5 no Godot.

   ```
   python treino/assistir.py treinos/primeiro/modelo.zip
   ```

   Passando um checkpoint do começo do treino, dá para gravar a versão que ainda não
   sabe nada.

## Como o agente aprende

- **O que ele vê:** a direção e a distância até o alvo, onde ele está na arena e a
  própria velocidade (6 números).
- **O que ele faz:** escolhe para onde andar (2 números entre -1 e 1).
- **Pontuação:** ganha um pouco a cada passo que se aproxima do alvo, perde um pouco a
  cada instante e ganha 1 ponto ao chegar. O episódio também acaba se o tempo esgotar.

As regras ficam em `godot/scripts/arena.gd`.

## Próximos passos

- Placar na arena (acertos e episódio) para aparecer no vídeo
- Câmera que segue o agente
- Sensor de raio e obstáculos, para virar labirinto
- Comparar checkpoints lado a lado (começo e fim do treino)
- Exportar o jogo para treinar sem o editor, mais rápido
- Ambientes novos: pular plataformas, fugir da sala com botão e porta, esconde-esconde
  com dois agentes
- Formato sem treino: modelos de linguagem competindo no mesmo ambiente
- Personagem próprio no lugar da cápsula

## Licença

MIT, ver `LICENSE`. O plugin [Godot RL Agents](https://github.com/edbeeching/godot_rl_agents_plugin),
de Edward Beeching, também é MIT e é baixado à parte.
