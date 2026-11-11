# sandbox-ia

**In English:** a prototype of a voice-driven game where the player teaches a clumsy
robot to bake a cake (and later other chores) just by talking to it. Everything runs
locally on an ordinary PC. A small language model only translates speech into actions
the robot's body already knows, and whatever the robot learns (new words, whole tasks,
safety habits) lives in an explicit memory that starts empty. This repo is the lab
that checks whether that is feasible before building the game: language understanding,
speech recognition, the robot body in Godot, and performance on a regular laptop. It
also holds a reinforcement learning sandbox (Godot RL Agents and Stable-Baselines3)
with a "master agent" that logs unusual episodes to turn into videos.

## A ideia

Um jogo em que você está numa cozinha, ao lado de um robô com forma de gente, e ensina
ele a fazer um bolo falando. Ele não sabe nada e obedece ao pé da letra:

- "Pega a faca", sem dizer por onde: ele pega pela lâmina e se corta.
- "Liga o forno", sem dizer a temperatura: ele gira o botão até o fim.
- "Põe o ovo na tigela": vai com casca e tudo.

O que você ensina fica guardado, então cada jogador termina com um robô diferente.
Depois do bolo, outras tarefas.

## Como o robô aprende

- **O corpo já vem pronto.** Ele sabe pegar, soltar, colocar, despejar, bater uma coisa
  contra outra, abrir, fechar, ligar, mexer, esperar e vestir a luva. Ninguém vai
  esperar horas de treino para o robô aprender a mexer o braço.
- **Um modelo de linguagem pequeno só traduz.** Ele roda no processador e transforma a
  fala nessas ações. A saída é travada por um esquema JSON, então ele não inventa verbo:
  se a fala usa uma palavra que o robô não conhece, a resposta é "não sei".
- **O que o robô aprende fica numa memória do jogo**, que começa vazia: palavras novas
  ("bater é pegar o garfo e mexer rápido"), tarefas inteiras (o jogador vai mandando e
  ele vai fazendo) e cuidados ("a faca se pega pelo cabo").
- **As falas do robô são frases prontas.** Nada que ele diz é texto livre gerado pelo
  modelo.

## Laboratório

Antes do jogo, quatro perguntas, da mais barata para a mais cara:

| Teste | Pergunta | Estado |
|---|---|---|
| Cabeça | Um modelo pequeno entende o jogador, e o robô aprende o bolo? | Primeira medição feita |
| Ouvido | O Whisper entende comandos de cozinha falados, rápido, no processador? | Áudios de teste gerados, falta medir |
| Corpo | O boneco no Godot pega, quebra o ovo, mexe e se machuca de um jeito que dá para entender? | A fazer |
| Tudo junto | Jogo, modelo e Whisper juntos num notebook comum ficam lisos? | A fazer |

### Cabeça: primeira medição

Notebook com i5-12450H, só processador, 73 frases de teste (`laboratorio/cabeca/casos.py`):

| Modelo (Qwen3.5, Q4_K_M) | Frases entendidas | Resposta mediana | Memória |
|---|---|---|---|
| 0,8 B | 26 de 73 | 0,5 s | 1,1 GB |
| 2 B | 28 de 73 | 1,0 s | 2,2 GB |
| 4 B | 39 de 73 | 2,4 s | 5,0 GB |

Com entendimento perfeito (o tradutor "oráculo"), a cozinha e a memória fazem o que
deviam: a aula didática termina num bolo perfeito, e a aula apressada termina num bolo
queimado, com casca de ovo e papel de pacote. Com o modelo no lugar, nenhum bolo saiu
ainda. O tradutor é o gargalo: ele se confunde quando o jogador está no meio de uma
aula e às vezes responde "não sei" para verbo que conhece.

### Como rodar

Precisa de Python 3.10 ou mais novo e do ffmpeg. Os programas e modelos (uns 6 GB)
ficam em `pesado/`, fora do git; a variável `SANDBOX_PESADO` muda o lugar.

```
python scripts/baixar_laboratorio.py
python -m laboratorio.cabeca.testar --oraculo     # confere a cozinha, sem modelo
python -m laboratorio.cabeca.testar               # testa os três modelos
python -m laboratorio.ouvido.gerar_audios         # áudios de teste com vozes sintéticas
```

```
laboratorio/
  comum.py              caminhos, servidor do modelo (llama.cpp) e medição de memória
  cabeca/cozinha.py     a cozinha em texto: primitivas do corpo, acidentes e o julgamento do bolo
  cabeca/tradutor.py    prompt e esquema JSON que travam a saída do modelo
  cabeca/robo.py        memória do que foi ensinado e execução das ações
  cabeca/casos.py       frases de teste e aulas inteiras
  cabeca/testar.py      roda tudo e grava os resultados
  ouvido/               geração dos áudios de teste (Windows e Piper)
scripts/baixar_laboratorio.py   baixa llama.cpp, whisper.cpp, modelos e vozes
```

## Sandbox de aprendizado por reforço

A primeira parte do repositório: um laboratório em Godot para treinar agentes por
tentativa e erro e gravar o processo em vídeo. Hoje tem um ambiente (alcançar o alvo).
No jogo, ele serve para dois lados: treinar algum movimento difícil do corpo e
comparar "aprendeu sozinho" com "eu ensinei".

```
godot/                  projeto Godot 4
  cenas/arena.tscn      uma arena: chão, paredes, agente e alvo
  cenas/treino.tscn     16 arenas lado a lado para treinar em paralelo
  cenas/demo.tscn       uma arena com câmera de perto
  cenas/replay.tscn     reproduz um episódio gravado, com câmera que acompanha
  scripts/              regras da arena, corpo do agente, ligação com o treino, gravador
treino/
  treinar.py            treina com PPO (Stable-Baselines3) e salva checkpoints
  mestre.py             agente mestre: marca o que foge do normal e escreve o diário
  filmar.py             filma um episódio gravado (Movie Maker do Godot)
  assistir.py           mostra um modelo salvo jogando
scripts/instalar_plugin.py   baixa o plugin Godot RL Agents para godot/addons
```

O **agente mestre** acompanha todos os episódios e decide o que vale virar vídeo. Ele
não grava imagem: cada arena grava o estado (posições e eventos), e o mestre marca
marcos (primeiro acerto, recorde, taxa de acerto passando de 10%, 25%, 50%, 75%, 90%),
anomalias (sair da arena, ficar parado, andar em círculo) e o que foge da curva dos
episódios recentes. Ele escreve um diário em `treinos/<nome>/diario.md` e guarda os
episódios marcados para filmar depois.

Para treinar: Godot 4, Python 3.10 ou 3.11, `python scripts/instalar_plugin.py`,
`pip install -r treino/requirements.txt` e `python treino/treinar.py --nome primeiro`
(depois abrir `cenas/treino.tscn` no Godot e apertar F6). Para filmar um episódio:
`python treino/filmar.py treinos/primeiro/episodios/000123.json`.

## Próximos passos

- Cabeça: tradutor mais confiável (prompt, histórico curto da conversa, regras para as
  frases simples e modelo para o resto)
- Ouvido: medir Whisper base, small e turbo nas vozes de teste, com e sem ruído, e
  depois com gente de verdade falando
- Corpo: cozinha 3D com o robô, cada movimento repetido 100 vezes em posições
  sorteadas; testar o ragdoll ativo com a física Jolt
- Tudo junto: quadros por segundo, memória e tempo de resposta no mesmo notebook
- Jogo: a primeira cozinha jogável

## Licença

MIT, ver `LICENSE`. O plugin [Godot RL Agents](https://github.com/edbeeching/godot_rl_agents_plugin)
é MIT, os modelos Qwen3.5 são Apache 2.0 e os dois são baixados à parte. O Piper, usado
só para gerar áudio de teste, é GPL e fica fora do repositório, num ambiente separado.
