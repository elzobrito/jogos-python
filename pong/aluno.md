# Pong em Pygame — guia do aluno

Cada parte é um `main.py` que **roda sozinho**. Se você ficar para trás, copie a pasta da parte anterior e continue. Sem imagens nem sons: tudo é desenhado com `pygame.draw`.

Teste de instalação: `python -m pygame.examples.aliens` (ou `python -c "import pygame"`). Se faltar: `pip install pygame`.

## Parte 1 — Janela e game loop  (`partes/parte-01-janela-loop/main.py`)

Abrir janela 800x500, loop eventos→atualizar→desenhar, `clock.tick` e `dt`.

**Checkpoint (mande no chat do Teams):** A janela abre com a linha central e fecha no X.

## Parte 2 — Raquetes  (`partes/parte-02-raquetes/main.py`)

Dois `pygame.Rect`, W/S e ↑/↓ com `VEL × dt`, `clamp_ip` para não sair da tela.

**Checkpoint (mande no chat do Teams):** As duas raquetes se movem e param na borda.

## Parte 3 — Bola e colisão  (`partes/parte-03-bola-colisao/main.py`)

Posição em float, rebate em topo/fundo, `colliderect` com raquetes — inverter **e reposicionar**.

**Checkpoint (mande no chat do Teams):** A bola rebate nas raquetes sem 'grudar'.

## Parte 4 — Placar, saque e vitória  (`partes/parte-04-placar-saque/main.py`)

Ponto quando a bola sai, saque para quem sofreu o ponto, vitória a 5, R reinicia.

**Checkpoint (mande no chat do Teams):** Placar sobe e aparece 'X venceu!'.

## Parte 5 — IA e variação  (`partes/parte-05-ia-variacao/main.py`)

IA que segue a bola com velocidade limitada (tecla 1/2), aceleração a cada rebatida.

**Checkpoint (mande no chat do Teams):** Dá para jogar sozinho contra a IA.

## Investigue o bug

Na parte 3, apague a linha `bx = esquerda.right` e veja a bola 'grudar' e tremer na raquete: a colisão continua verdadeira no quadro seguinte. Pergunta: por que inverter a velocidade não basta?

## Fechamento — sua variação

Escolha **uma** variação (ou invente) e aplique no **seu** jogo. Entregue o `main.py` e uma frase: *o que mudei e qual conceito usei*.

- Raquete encolhe a cada ponto sofrido
- Bola com cor/rastro conforme a velocidade
- Modo 'parede': um jogador contra a parede contando rebatidas
- Obstáculo no meio do campo (um Rect fixo)
- Tema do seu projeto: troque cores, nomes e regra de vitória
