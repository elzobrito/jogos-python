# Roteiro falado — Snake em Pygame, do zero ao jogo com velocidade

## Abertura

Se você já montou um site em Flask, o programa espera. Chega um pedido, você responde, e o servidor fica parado até o próximo clique. Jogo não funciona assim. Jogo é um projetor de cinema: o filme não espera você apertar um botão a cada fotograma. Ele avança sozinho, dezenas de vezes por segundo, e se um quadro atrasar ou um evento se perder, a cobra some, a janela trava, ou o teclado simplesmente não obedece.

Os sintomas que você vai ver hoje são bem concretos. A janela abre e o processador vai a cento e dez por cento. A cobra anda torta, fora da grade. Você come a maçã e ela não cresce. Você aperta a seta contrária e morre na hora, como se o jogo tivesse trapaceado.

Neste vídeo eu construo o Snake do zero, em cinco partes, e cada parte roda sozinha. Em cada uma eu mostro primeiro o jeito que quebra, e só depois o código que resolve. Porque copiar o jogo pronto não adianta na hora em que a próxima tela for o Pong.

Bora para o código.

## O que você precisa

Python 3 e Pygame. No terminal, roda `python -c "import pygame; print('Pygame instalado com sucesso:', pygame.__version__)"`. Se reclamar, `pip install pygame-ce` e testa de novo.

Cada parte tem o próprio `main.py` no link da descrição. Se você se perder, abre a pasta da parte em que parou e continua dali. Sem imagem, sem som, sem arquivo extra: só `pygame.draw.rect` e fonte do sistema.

## Parte 1 — A janela e o game loop

Primeiro o coração. Um jogo é um `while rodando` que, a cada volta, faz três coisas na mesma ordem: lê o que aconteceu, atualiza o mundo, desenha o quadro. Sem esse ciclo, você não tem jogo. Tem um script que pintou uma vez e morreu.

O jeito ingênuo, o que quase todo mundo tenta na primeira vez, é um laço sem freio:

`while True:`

Ele gira o mais rápido que o processador aguentar. A janela até abre. Só que o ventilador grita, o uso de CPU dispara, e qualquer movimento futuro fica impossível de controlar, porque o mundo avança milhares de vezes por segundo.

Repara o que o código certo faz. A gente chama `pygame.init()`, abre `pygame.display.set_mode` com `LARGURA` 800 e `ALTURA` 600, pinta o fundo com `tela.fill(PRETO)` e mostra o quadro com `pygame.display.update()`. E a linha que segura tudo isso é `relogio.tick(8)`.

Oito quadros por segundo. Parece pouco perto de um filme a 24. Para uma cobra que anda de bloco em bloco, é exatamente a velocidade em que o olho humano ainda consegue virar. Sem o `relogio.tick(8)`, o laço não dorme. Com ele, o Pygame espera o que faltar para completar aquele intervalo, devolve o controle, e o jogo fica jogável.

Nos eventos, por enquanto só uma coisa importa: `pygame.QUIT`. Clicou no X, `rodando` vira `False`, o `while` termina, `pygame.quit()` e `sys.exit()`. Se você esquecer de esvaziar a fila com `pygame.event.get()`, o sistema operacional acha que a janela travou.

Ah, Elzo, mas por que oito e não sessenta? Porque a gente ainda não tem física contínua. A cobra vai pular de 20 em 20 pixels. Sessenta pulos por segundo a deixa incontrolável. Tudo é trade-off: neste jogo a gente troca fluidez cinematográfica por tempo de reação. No Pong isso muda.

Roda aí. Tem que abrir uma janela preta 800 por 600, com o título Snake em Python, e fechar no X sem deixar processo zumbi. Pausou? Então me responde nos comentários: o que o `relogio.tick(8)` impede de acontecer com a CPU?

## Parte 2 — A cobra e o movimento

Agora a cobra. E aqui a imagem mental é um trem. A locomotiva é a cabeça. Cada vagão é um quadrado. Para o trem andar, você não empurra o corpo inteiro: você coloca uma locomotiva nova na frente e solta o último vagão. A lista `cobra` é exatamente isso: pares de x e y, cabeça no índice zero.

O jeito ingênuo é pegar um `x` e um `y` soltos e somar 1, 2, 5 pixels a cada quadro, à vontade. Aí o quadrado escorrega no meio da célula, a comida nunca coincide, e a colisão vira loteria.

Por isso existe `TAMANHO = 20`. Todo passo é `velocidade_x = TAMANHO` ou `velocidade_y = -TAMANHO`. A cobra nasce com `[400, 300]` na cabeça, `[380, 300]` no meio e `[360, 300]` na cauda: três blocos alinhados no centro, andando para a direita. A nova cabeça é sempre `cabeca[0] + velocidade_x` e `cabeca[1] + velocidade_y`. Depois, `cobra.insert(0, nova_cabeca)` e `cobra.pop()`. Insert na frente, pop atrás. O trem andou, o comprimento continua 3.

As setas entram no mesmo `pygame.event.get()` da parte 1, agora com `pygame.KEYDOWN`. `pygame.K_UP` zera o x e põe y negativo. Baixo, esquerda, direita, a mesma ideia. É evento de um toque só, igual virar. Segurar a tecla não precisa repetir: a cobra já está andando sozinha naquela direção, quadro após quadro.

Limite honesto: se algum dia você somar um número que não é múltiplo de 20, os blocos saem da grade e nunca mais encontram a maçã. A constante `TAMANHO` tem que aparecer em todo deslocamento, não só na criação.

Roda aí. Três quadrados verdes têm que deslizar nas quatro direções, sempre colados na grade. Teste as setas. E me fala: por que a gente insere em `cobra[0]` e tira do fim, em vez de somar 20 em todos os segmentos?

## Parte 3 — Comida, crescimento e placar

Comer. A recompensa do Snake é ridiculamente simples: a cabeça cai na mesma casa da maçã. Não tem colisão de retângulo ainda. É igualdade de lista: `nova_cabeca == comida`.

O erro clássico é deixar o `cobra.pop()` sempre. Você come, insere a cabeça nova, tira a cauda, e o comprimento não muda. A maçã some, os pontos até podem subir, e a cobra continua do mesmo tamanho. Visualmente, você comeu vento.

A correção é um `if` e um `else`. Comeu? `pontos += 10` e sorteia outra `comida` com `random.randrange(0, LARGURA, TAMANHO)`. O terceiro argumento é o passo. Sem ele, a maçã nasce no pixel 13, a cobra só pisa em 0, 20, 40, e os dois nunca se encontram. Não comeu? Aí sim, `cobra.pop()`.

O placar é estado, não enfeite. `fonte.render` escreve `Pontos: {pontos}` e o `tela.blit` cola isso em (20, 20), depois do `tela.fill(PRETO)`, senão o texto some atrás do fundo. A maçã é um `pygame.draw.rect` vermelho no mesmo tamanho do bloco.

Tem um limite que a gente aceita nesta parte: `random.randrange` pode sortear uma casa que já está embaixo da cobra. Aí você ganha ponto sem ter andado. Resolver isso é um `while comida in cobra`. Não está neste `main.py` de propósito. Primeiro o crescimento tem que existir.

Roda aí. Come três maçãs. O corpo tem que ganhar um quadrado a cada uma, e o número no canto sobe de dez em dez. Se a cobra passou por cima e não cresceu, você esqueceu o `else` do `pop`. Qual linha, nos comentários, é a responsável pelo crescimento: o insert ou a ausência do pop?

## Parte 4 — Colisão, 180 graus e Game Over

Até aqui a cobra atravessa a parede e dobra sobre si mesma. Não é jogo, é rascunho. Parte 4, as regras de morte.

Borda primeiro. Se `nova_cabeca[0] < 0` ou `>= LARGURA`, ou o y sai de 0 até `ALTURA`, `rodando` vira `False`. A gente testa isso ANTES de inserir a cabeça, para não desenhar um bloco fora da tela.

Corpo em seguida: `if nova_cabeca in cobra[1:]`. O `[1:]` não é frescura. A cabeça atual é o índice zero. Se você perguntar se a nova posição está na lista inteira depois de um `insert`, ou se comparar a cabeça com ela mesma, o jogo acaba no primeiro quadro. A fatia ignora o pescoço que ainda é a cabeça antiga e pega só o restante do trem.

Agora o bug que mata gente inocente. Você está indo para a direita, `velocidade_x` vale `TAMANHO`. Aperta esquerda. Sem guarda, a nova cabeça é `[380, 300]`, que é exatamente o segundo bloco. `nova_cabeca in cobra[1:]` dá verdadeiro, e aparece `GAME OVER`. O jogador jura que o teclado falhou. Não falhou. O trem tentou colocar a locomotiva em cima do primeiro vagão.

Por isso as setas ganham um `and`. Para cima, `pygame.K_UP and velocidade_y == 0`: só vira para vertical se hoje você está no horizontal. Para esquerda, `pygame.K_LEFT and velocidade_x == 0`. A inversão de 180 graus simplesmente não entra no estado.

Quer ver o bug com os próprios olhos? Na seta para a esquerda, apague o `and velocidade_x == 0`, rode, vá para a direita e aperte a contrária. A cabeça entra no pescoço e a função `game_over` pinta `GAME OVER` no centro, com os pontos embaixo, e espera o X. Depois coloca a guarda de volta.

Ah, Elzo, mas o jogador mandou virar. Por que o código recusa? Porque recusar aqui é usabilidade, não ditadura. É prevenção de erro: o toque rápido na tecla oposta é acidente, não intenção. O custo é que você precisa de um L para inverter, dois toques, não um. Neste clássico, esse custo vale a pena.

Roda aí. Bata nas quatro paredes. Depois faça uma curva fechada contra o próprio corpo. Tem que aparecer a tela vermelha de fim, não um crash. E me responde: por que a checagem usa `cobra[1:]` e não a lista inteira?

## Parte 5 — Velocidade progressiva

O Snake clássico, parado em 8 quadros, fica fácil demais depois de dois minutos. Parte 5, a dificuldade sobe com o estado.

O erro desta vez é incrementar a velocidade a cada quadro, dentro do `while`, comendo ou não. Em dez segundos o jogo vira um strobe. Ninguém reage. A variável `velocidade` deixa de ser um parâmetro de design e vira um relógio que só acelera.

No código, `velocidade` começa em 8. Ela só muda no mesmo `if` da maçã, ao lado de `pontos += 10`: `velocidade += 0.5`. E o laço passa a chamar `relogio.tick(velocidade)` em vez de `relogio.tick(8)`. Uma maçã, meio quadro a mais por segundo. Dez maçãs, cinco a mais. A curva é suave o bastante para o jogador acompanhar.

Repara o que este `main.py` ainda não faz. Ele não mostra "Nível: 2" na tela. Ele não espera 5 maçãs para dar um degrau. E ele não tem teto. O plano pedagógico pedia `pontos // 5` e um limite máximo; o gabarito desta parte acelera a cada comida, meio a meio. Os dois estão certos como ideia. Só o segundo está neste arquivo. Se você deixar `velocidade` subir sem teto, lá pelo terceiro minuto o tick fica alto demais e a cobra atravessa a maçã sem você conseguir virar. Esse é o trade-off que o desafio daqui a pouco vai pedir para você resolver.

Callback rápido: o `relogio.tick` da parte 1 continua sendo o mesmo relógio. A gente só trocou o argumento constante por uma variável de estado. Eventos, atualizar, desenhar: a ordem não mudou.

Roda aí. Come umas seis maçãs e sente o ritmo. Tem que ficar claramente mais rápido, sem travar. Nos comentários: por que somar `0.5` na hora da comida, e não no fim de cada quadro, preserva o controle do jogador?

## Desafio — sua variação

O Snake deste vídeo ainda é o meu. Agora eu quero o seu.

Escolhe uma variação e aplica. Velocidade por nível: a cada 5 maçãs a cobra acelera e o topo da tela mostra `Pontos: 50 | Nível: 2`, com um máximo para não ficar impossível. Maçã dourada que some em 5 segundos, vale 30 e faz o corpo piscar amarelo. Obstáculos fixos no centro, que matam igual parede. Ou wrap-around, modo Pac-Man: sai de um lado, entra do outro, e a única morte é o próprio corpo.

A regra é uma só: tem que mudar regra ou mecânica. Trocar o verde por azul não conta. Depois conta nos comentários o que mudou no estado e como isso aparece na tela.

## Fechamento

Lembra dos sintomas do começo? Janela que come CPU, cobra torta, maçã que não engorda, seta contrária que mata. Cada um tinha um jeito ingênuo e uma linha que resolve: `relogio.tick`, passo de `TAMANHO`, `pop` só quando não come, guarda de 180 graus, `velocidade` no tick. Você levou o game loop, a lista como trem, a colisão discreta e a ideia de que dificuldade também é estado.

Guarda isso. No próximo vídeo vem o Pong, e a gente reaproveita o laço, os eventos e o relógio, só que a bola deixa a grade e passa a andar em pixels livres, com colisão de retângulo.

Se o vídeo te ajudou, deixa o like e se inscreve para não perder o Pong. Dúvida, comentário. Um abraço, e a gente se vê na rebatida.

<!-- ilustrativo
while True:
x += 5
cobra.pop()
if nova_cabeca in cobra:
velocidade += 1
relogio.tick(velocidade_base + (pontos // 5) * 1)
Pontos: 50 | Nível: 2
-->
