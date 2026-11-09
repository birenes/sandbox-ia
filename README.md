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
  scripts/gravador.gd   anota cada episódio (trajetória e eventos)
  cenas/replay.tscn     reproduz um episódio gravado, com câmera que acompanha
treino/
  treinar.py            treina com PPO (Stable-Baselines3) e salva checkpoints
  mestre.py             agente mestre: marca o que foge do normal e escreve o diário
  filmar.py             filma um episódio gravado (Movie Maker do Godot)
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

## Agente mestre

O mestre acompanha todos os episódios de todas as arenas e decide o que vale virar
vídeo. Ele não grava imagem: cada arena grava o estado do episódio (posições e
eventos), o que ocupa pouco espaço e permite filmar depois com a câmera que quiser.

Ele marca três tipos de coisa:

- **Marcos:** primeiro acerto, recorde de tempo, taxa de acerto passando de 10%, 25%,
  50%, 75% e 90%, piora e recuperação.
- **Anomalias:** agente saindo da arena (bug de física), parado o episódio inteiro,
  andando muito e terminando perto de onde começou.
- **Fora da curva:** pontuação ou número de batidas na parede muito diferente dos
  episódios recentes. O normal muda ao longo do treino, então a comparação também.

Durante o treino ele roda junto e escreve em `treinos/<nome>/`:

- `diario.md`: o diário de bordo, para ler
- `diario.jsonl`: o mesmo, para outro programa ler
- `episodios/`: os episódios marcados, inteiros
- `episodios/amostra/`: um a cada 50 episódios normais, para comparar começo e fim

Para filmar um episódio guardado:

```
python treino/filmar.py treinos/primeiro/episodios/000123.json
python treino/filmar.py treinos/primeiro/episodios/000123.json --resolucao 1080x1920
```

Uma janela pequena abre, o Godot renderiza quadro a quadro e o vídeo sai em .mp4 ao
lado do episódio (precisa do ffmpeg para o .mp4; sem ele, sai em .avi).

Também dá para testar sem treino, com um piloto automático que vai no rumo do alvo
errando um pouco, e rodar o mestre depois:

```
godot --path godot res://cenas/treino.tscn -- --piloto --gravar_em=C:/caminho/teste
python treino/mestre.py C:/caminho/teste/episodios.jsonl --saida treinos/teste
```

## Próximos passos

- Revisão do diário por um modelo de linguagem, sugerindo a ordem do vídeo
- Câmera do replay enquadrando agente e alvo juntos
- Replay de vários episódios lado a lado (começo e fim do treino)
- Sensor de raio e obstáculos, para virar labirinto
- Exportar o jogo para treinar sem o editor, mais rápido
- Ambientes novos: pular plataformas, fugir da sala com botão e porta, esconde-esconde
  com dois agentes
- Formato sem treino: modelos de linguagem competindo no mesmo ambiente
- Personagem próprio no lugar da cápsula

## Licença

MIT, ver `LICENSE`. O plugin [Godot RL Agents](https://github.com/edbeeching/godot_rl_agents_plugin),
de Edward Beeching, também é MIT e é baixado à parte.
