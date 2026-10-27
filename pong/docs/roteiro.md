# Roteiro falado — Pong em Pygame, do zero ao jogo contra a IA

## Abertura

Lá no Snake, o mundo era uma planilha. A cobra saltava de vinte em vinte pixels numa grade invisível, e testar colisão era só perguntar se duas casas eram iguais. Quando você tira essa grade para construir o Pong, o chão some. A bola corre solta em qualquer diagonal, com casas decimais, e dois retângulos precisam se encontrar dezenas de vezes por segundo.

Os sintomas aparecem na hora. No seu computador a partida voa; num notebook mais simples, parece câmera lenta. Você segura a tecla para subir a raquete, ela dá um passo curto e para. A bola encosta na raquete e, em vez de rebater, fica presa ali dentro, tremendo como se tivesse cola. Alguém pontua e o placar dispara sozinho. Ou você liga a IA e descobre que é impossível vencer.

Neste vídeo eu construo o Pong do zero em cinco partes, e cada parte roda sozinha. Em todas eu mostro primeiro o jeito ingênuo que quebra, e só depois a linha que resolve. Porque copiar código pronto não te salva quando o próximo jogo for o Breakout.

Bora para o código.

## O que você precisa

Python 3 e Pygame. No terminal, roda `python -c "import pygame"` ou `python -m pygame.examples.aliens`. Se reclamar que não achou o módulo, instala com `pip install pygame` e testa de novo.

Cada parte tem o próprio `main.py` separado em pastas no link da descrição. Se você travar em algum passo, abre a pasta da parte em que parou e segue dali. Sem imagem externa, sem som, sem fonte baixada: tudo é desenhado com `pygame.draw` e a fonte padrão do Pygame.

## Parte 1 — Janela e game loop

Primeiro o coração do jogo: o game loop. Em toda volta do `while rodando:`, o programa faz três coisas na mesma ordem: lê os eventos, atualiza o mundo e desenha o quadro.

O jeito ingênuo de quem vem do Snake é somar pixels fixos por quadro, como `x += 5`. Num computador a 60 FPS, cinco pixels por volta viram 300 pixels por segundo. Num notebook a 30 FPS, viram 150 pixels por segundo. É como combinar uma corrida dando um passo a cada piscada de olho: quem pisca mais rápido corre o dobro, e o jogo muda de velocidade em cada máquina.

A Parte 1 resolve isso na raiz. Definimos `LARGURA, ALTURA = 800, 500`, `FPS = 60`, `COR_FUNDO = (15, 15, 25)` e `COR_OBJ = (235, 235, 235)`. Chamamos `pygame.init()`, abrimos `pygame.display.set_mode((LARGURA, ALTURA))`, colocamos `pygame.display.set_caption("Pong")` e criamos `relogio = pygame.time.Clock()`. Na primeira linha do `while rodando:`, entra a chave da aula:

`dt = relogio.tick(FPS) / 1000`

Essa linha segura o laço em 60 FPS e devolve os milissegundos desde o último quadro. Dividindo por mil, `dt` guarda os segundos do quadro, cerca de 0,016 a 60 FPS. Toda velocidade será em pixels por segundo multiplicada por `dt`. Se o quadro atrasar, `dt` cresce junto e compensa o passo.

Nos eventos, `for evento in pygame.event.get():` olha o `pygame.QUIT` para mudar `rodando = False` e chegar ao `pygame.quit()`. O bloco de atualizar fica vazio de propósito para as próximas partes. E no desenho limpamos o fundo com `tela.fill(COR_FUNDO)`, traçamos a linha central com `pygame.draw.line(tela, (70, 70, 90), (LARGURA // 2, 0), (LARGURA // 2, ALTURA), 2)` e exibimos com `pygame.display.flip()`. Sem o `tela.fill(COR_FUNDO)`, cada quadro novo pintaria por cima do anterior.

Ah, Elzo, mas se a máquina travar, o `dt` não faz a bola pular? Faz, sim. Tudo é trade-off: o `dt` iguala 30 e 60 FPS, mas não resolve colisão sozinho.

Roda aí. Tem que abrir a janela 800 por 500 com a linha central e fechar no X. Funcionou? Responde nos comentários: por que uma raquete com `dt` anda igual em 30 e em 60 FPS?

## Parte 2 — Raquetes

Agora entram os jogadores com o `pygame.Rect`, que guarda posição e tamanho juntos e traz prontos os limites e testes de colisão.

O erro comum aqui é tentar mover a raquete com o evento `pygame.KEYDOWN`, como fazíamos para virar a cobra no Snake. Se você usar `pygame.KEYDOWN` na raquete, aperta o W, ela dá um passo curto e congela, mesmo mantendo o dedo na tecla. O evento só avisa o instante em que a tecla desce, não se continua segurada.

Para ter movimento contínuo, usamos `pygame.key.get_pressed()`. Criamos `VEL_RAQUETE = 380` em pixels por segundo e os retângulos `esquerda = pygame.Rect(30, ALTURA // 2 - 45, 12, 90)` e `direita = pygame.Rect(LARGURA - 42, ALTURA // 2 - 45, 12, 90)`. Depois escrevemos `def mover_raquete(r, cima, baixo, dt):`.

Dentro dela, `teclas = pygame.key.get_pressed()` lê quais teclas estão seguradas naquele quadro. Se `teclas[cima]:` está ativa, `r.y -= int(VEL_RAQUETE * dt)`. Se `teclas[baixo]:` está ativa, `r.y += int(VEL_RAQUETE * dt)`. E `r.clamp_ip(tela.get_rect())` prende o retângulo dentro da tela.

Na atualização chamamos `mover_raquete(esquerda, pygame.K_w, pygame.K_s, dt)` e `mover_raquete(direita, pygame.K_UP, pygame.K_DOWN, dt)`. No desenho, dois `pygame.draw.rect` pintam `esquerda` e `direita`.

Limite honesto: como o `pygame.Rect` só guarda inteiros, `int(VEL_RAQUETE * dt)` trunca decimais. Em velocidades muito baixas isso zeraria o passo; na bola vamos resolver com float.

Roda aí e segura W, S e as setas. As duas raquetes têm que se mover suaves e parar na borda. Conta nos comentários: o que acontece se você apagar o `r.clamp_ip(tela.get_rect())`?

## Parte 3 — Bola e colisão

Parte 3, a bola entra em jogo e aparece o bug mais famoso do Pong.

Definimos `VEL_BOLA = 300`, `bola = pygame.Rect(LARGURA // 2 - 8, ALTURA // 2 - 8, 16, 16)` e `vx, vy = VEL_BOLA, VEL_BOLA * 0.6`. Para o arredondamento inteiro não entortar a diagonal, guardamos a posição real em float:

`bx, by = float(bola.x), float(bola.y)`

A cada quadro somamos `bx += vx * dt` e `by += vy * dt`, copiando para `bola.topleft = (round(bx), round(by))`. A função `def sacar(direcao):` centraliza a bola e sorteia `vy = VEL_BOLA * random.uniform(-0.7, 0.7)`. No teto e no chão, `if bola.top <= 0 or bola.bottom >= ALTURA:` inverte `vy = -vy` e corrige `by = min(max(by, 0), ALTURA - bola.height)`. Se sair nas laterais, `sacar(1)` ou `sacar(-1)` relança do centro.

Na raquete, o jeito ingênuo que quase todo mundo escreve primeiro é:

`if bola.colliderect(esquerda): vx = -vx`

Olha por que quebra. Quando a bola entra fundo na raquete, avança mais do que consegue sair num passo. No primeiro quadro `bola.colliderect(esquerda)` dá verdadeiro e inverte `vx`. No quadro seguinte ela anda um pouco, mas continua sobreposta à raquete. O `colliderect` dá verdadeiro de novo, inverte `vx` outra vez, e a bola fica grudada, tremendo sem parar.

A resposta precisa inverter a velocidade e tirar a bola de dentro da raquete:

`if bola.colliderect(esquerda) and vx < 0:`
`    vx = -vx`
`    bx = esquerda.right`

A guarda `and vx < 0` garante que só rebate bola vindo para a esquerda, e `bx = esquerda.right` encosta a bola fora da raquete. Na direita é o espelho: `if bola.colliderect(direita) and vx > 0:`, inverte `vx = -vx` e ajusta `bx = direita.left - bola.width`. No desenho, `pygame.draw.ellipse(tela, COR_OBJ, bola)` pinta a bola.

Teste o bug proposital: se apagar só `bx = esquerda.right` mantendo `and vx < 0`, a guarda impede a segunda inversão, então a bola não gruda, mas atravessa a raquete por dentro. Se tirar também o `and vx < 0`, deixando só `if bola.colliderect(esquerda): vx = -vx`, a bola gruda e treme na quina.

Limite: uma bola muito rápida atravessaria a raquete num quadro, o tunneling, fora do escopo.

Roda aí e rebate sem grudar. Nos comentários: qual linha reposiciona a bola, e por que só inverter `vx` não basta?

## Parte 4 — Placar, saque e vitória

Até aqui ninguém ganha nem perde. A Parte 4 cria o estado do jogo: `PONTOS_VITORIA = 5`, `placar = [0, 0]` e `vencedor = None`, com `fonte = pygame.font.Font(None, 64)` e `fonte_peq = pygame.font.Font(None, 28)`.

O erro comum é somar ponto quando a bola sai da tela e esquecer de recolocá-la no centro. No quadro seguinte a bola segue lá fora, `bola.right < 0` continua verdadeiro a 60 FPS, e o placar dispara sozinho.

Por isso ponto e saque andam juntos. Saiu na esquerda em `if bola.right < 0:`? Soma `placar[1] += 1` e chama `sacar(1)`. Saiu na direita em `if bola.left > LARGURA:`? Soma `placar[0] += 1` e chama `sacar(-1)`. Depois, `if max(placar) >= PONTOS_VITORIA:` grava `vencedor = "Esquerda" if placar[0] > placar[1] else "Direita"`.

O estado governa o loop: o `if True:` vira `if vencedor is None:`. Aos 5 pontos, a bola para. Nos eventos, `if evento.type == pygame.KEYDOWN and evento.key == pygame.K_r and vencedor:` zera `placar, vencedor = [0, 0], None` e chama `sacar(random.choice((-1, 1)))`. E no desenho mostramos o placar no topo e `f"{vencedor} venceu! R para reiniciar"` no centro.

Ah, Elzo, mas espalhar o estado em várias variáveis soltas não fica difícil de manter? Fica; o Breakout organiza melhor isso.

Roda aí até 5 pontos e testa o R. Nos comentários: o que acontece com o placar se esquecer de chamar `sacar`?

## Parte 5 — IA e variação

Na Parte 5 criamos um adversário controlado pelo computador e aceleramos as rebatidas.

O erro comum ao criar a IA é fazê-la perseguir a bola com velocidade total. Uma IA perfeita é impossível de vencer e tira toda a graça do jogo.

Por isso `def mover_ia(r, dt):` persegue `alvo = bola.centery` com velocidade limitada: `passo = int(VEL_RAQUETE * 0.75 * dt)` e folga de 10 pixels em `if r.centery < alvo - 10:` e `elif r.centery > alvo + 10:`. Experimente trocar `0.75` por `1.5` para ver como fica imbatível, e depois volte para `0.75`.

No topo criamos `contra_ia = True` e usamos `pygame.KEYDOWN` em `pygame.K_1` e `pygame.K_2` para alternar entre jogar contra a IA ou dois jogadores, exibindo `modo = "1: contra IA" if contra_ia else "2: dois jogadores"` no rodapé. Repara no callback: `pygame.KEYDOWN` falhava para mover a raquete na Parte 2, mas é ideal para trocar de modo com um toque só. E nas colisões das raquetes colocamos `vx *= 1.05`, acelerando 5% a cada batida.

Roda aí e joga sozinho contra a IA no modo 1. Nos comentários: qual número em `mover_ia` você mudaria para deixar a IA mais fácil, e por quê?

## Desafio — sua variação

Agora o Pong é seu. Escolhe uma variação do cartão, ou inventa a sua, e aplica no seu `main.py`:

1. Raquete encolhe a cada ponto sofrido.
2. Bola com cor ou rastro conforme a velocidade.
3. Modo parede: um jogador contra a parede contando rebatidas.
4. Obstáculo no meio do campo usando um `pygame.Rect` fixo.
5. Tema do seu projeto: troque cores, nomes e regra de vitória.

Critério: a variação precisa mudar uma regra ou mecânica, não só a cor. Depois comenta o que mudou e qual trecho do código alterou.

## Fechamento

Lembra dos sintomas do início? Velocidade diferente em cada PC se resolve com `dt = relogio.tick(FPS) / 1000`. Raquete travada se resolve com `pygame.key.get_pressed()` e `r.clamp_ip(tela.get_rect())`. Bola grudada se resolve com `and vx < 0` e `bx = esquerda.right`. Placar disparando se resolve no `sacar`, e IA justa usa `VEL_RAQUETE * 0.75`.

Guarda o game loop, o `dt` e o `pygame.Rect`. No próximo vídeo vem o Breakout, reaproveitando tudo isso contra dezenas de tijolos. Deixa o like, se inscreve e comenta sua variação. Até o próximo vídeo!

<!-- ilustrativo
x += 5
if bola.colliderect(esquerda): vx = -vx
0.75
1.5
-->
