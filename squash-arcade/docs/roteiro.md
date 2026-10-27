# Roteiro falado — Squash Arcade em Pygame — do Pong ao som no jogo

## Abertura

Se você acompanhou a construção do Pong, você lembra que a partida era totalmente muda. A bola ia e vinha, rebatia nas raquetes, batia nas bordas da tela, mas sem emitir um único ruído. Parecia um jogo preso no cinema mudo.

Aí você decide colocar áudio no seu jogo pela primeira vez. Parece a coisa mais simples do mundo: você pega um arquivo de som, carrega no programa e manda tocar quando a bola bater. Só que é exatamente aí que começam a aparecer uns problemas estranhos que pegam todo desenvolvedor de surpresa. O primeiro som de colisão sai com um atraso nítido, dando uma sensação esquisita de descompasso com a imagem. Depois, quando a bola bate na parede e na raquete quase ao mesmo tempo, ou quando você perde uma vida enquanto toca um bipe, o efeito sonoro principal é cortado no meio por outro som mais fraco. E para completar, o barulho fica alto demais no fone de ouvido, sem nenhuma tecla para silenciar a partida.

E se a configuração do mixer vier depois do `pygame.init()`, o primeiro bipe ainda sai atrasado, como se a imagem e o áudio estivessem em faixas diferentes.

No vídeo de hoje, eu vou construir o Squash Arcade do zero, em cinco partes executáveis, e cada pasta roda de forma independente. Em cada uma delas, eu vou te mostrar primeiro o problema concreto que acontece na tela, e só depois a linha de código que resolve a situação. Porque mais importante do que copiar um código pronto é entender por que o jeito ingênuo quebra. É essa bagagem que você vai levar para os seus próximos jogos.

Então, para a gente não perder tempo, bora para a tela.

## O que você precisa

Antes de começar, o básico. Você só vai precisar do Python 3 e da biblioteca Pygame instalada no seu computador. Para conferir se o seu ambiente já está pronto, abre o terminal e digita `python -c "import pygame"`. Se o comando rodar limpo e voltar para o prompt sem reclamar de nada, show de bola, você já pode começar. Se aparecer algum erro dizendo que o módulo não foi encontrado, basta rodar `pip install pygame-ce` ou `pip install pygame` e testar novamente.

Todo o código deste projeto está organizado em cinco pastas separadas no link da descrição. Cada pasta representa uma parte da aula e contém o seu próprio `main.py`. Os WAV ficam na pasta `sons/` na raiz do projeto, e as partes 3, 4 e 5 carregam com o caminho relativo `../../sons/`. Se em qualquer momento você se perder nas alterações, não se preocupe: basta abrir a pasta da parte onde você parou e continuar dali.

## Parte 1 — Quadra e raquete

Vamos começar pela estrutura da nossa quadra e pelo movimento da raquete na base da tela.

Quem vem de jogos baseados em passos por quadro, ou quem está acostumado a tratar o teclado apenas com o evento `pygame.KEYDOWN`, quase sempre comete o mesmo erro na primeira tentativa. Você coloca a movimentação da raquete dentro do laço de eventos, roda o programa, aperta a seta para a direita e olha o que acontece: a raquete dá um pequeno tranco de poucos pixels e para imediatamente, mesmo que você continue com o dedo afundado na tecla. O evento `pygame.KEYDOWN` só é disparado uma única vez, no milissegundo exato em que a tecla é pressionada. Ele não avisa se você continuou segurando a tecla nos quadros seguintes.

Pensa na diferença entre um botão de campainha e uma torneira de água. O evento de tecla é a campainha: você aperta, ela toca uma vez e silencia. Já o movimento suave de uma raquete precisa funcionar como uma torneira aberta: enquanto a mão estiver lá segurando, a água continua correndo sem interrupção.

Para fazer a raquete deslizar de verdade, nós usamos o `pygame.key.get_pressed()`. Em vez de esperar por um evento passageiro, essa função tira uma fotografia completa do teclado a cada volta do laço principal. Nós lemos o estado das setas direcionais e das teclas A e D nesta linha:

`direcao = int(bool(teclas[pygame.K_RIGHT] or teclas[pygame.K_d])) - int(...`

Se a tecla da direita estiver pressionada, o primeiro termo vale um. Se a da esquerda estiver pressionada, o segundo termo vale um. A subtração nos devolve um para a direita, menos um para a esquerda, ou zero se nenhuma tecla estiver ativa.

Em seguida, multiplicamos essa direção pela nossa velocidade e pelo tempo decorrido no quadro:

`raquete.x += round(direcao * VELOCIDADE_RAQUETE * dt)`

Definimos `VELOCIDADE_RAQUETE = 560` em pixels por segundo. E o relógio calcula o delta time com uma trava de segurança: `dt = min(relogio.tick(FPS) / 1000.0, 0.033)`, garantindo `FPS = 60`. Para manter a raquete presa dentro da quadra delimitada por `CAMPO = pygame.Rect(55, 125, 790, 460)`, aplicamos duas travas de posição: `raquete.left = max(CAMPO.left + 6, raquete.left)` e `raquete.right = min(CAMPO.right - 6, raquete.right)`.

Ah, Elzo, mas se o computador tiver uma travada brusca, o `dt` não pode fazer a raquete dar um salto gigante? Pode acontecer, sim. Por isso colocamos o limite de `0.033` segundos no relógio. Além disso, como o retângulo da raquete só aceita números inteiros, a função `round` arredonda o deslocamento. Se você usasse uma velocidade minúscula de cinco pixels por segundo, a multiplicação daria menos de meio pixel e o arredondamento cortaria para zero, travando a raquete. Com quinhentos e sessenta pixels por segundo, o passo é consistente e suave. Tudo na arquitetura de jogos é trade-off.

Roda aí o código da Parte 1. Segura as setas ou as teclas A e D: a raquete verde precisa deslizar suavemente e parar firme rente às bordas da quadra sem vazar. Teste os comandos e me responda uma coisa nos comentários: por que a leitura contínua com `pygame.key.get_pressed()` resolve o problema do engasgo que acontecia no evento de tecla?

Com a quadra e a raquete prontas, o próximo passo é soltar a bola e construir a física das rebatidas.

## Parte 2 — Bola e rebatidas

Na Parte 2, nós colocamos a bola em jogo, calculamos o ricochete nas paredes e no teto, e implementamos o controle de ângulo na raquete.

O erro mais comum ao programar uma colisão desse tipo é usar apenas um teste simples de sobreposição geométrica. O desenvolvedor escreve uma condição básica verificando se a bola encostou na raquete e manda inverter a velocidade vertical. Parece que funciona, mas basta jogar alguns segundos para ver o desastre acontecer: quando a bola raspa na lateral da raquete ou atinge a quina durante a descida, ela fica presa dentro da madeira, invertendo de direção dezenas de vezes por segundo em um tremelique sem fim. E se a bola vier por baixo da raquete, ela é puxada magicamente para cima.

Imagina uma cama elástica em uma academia. Para conseguir pular e ganhar impulso, você precisa vir de cima para baixo e aterrissar sobre a lona. Se você tentar passar engatinhando por baixo da cama elástica e ela te arremessar para o teto como se você tivesse pulado de cima, a física do mundo perde completamente o sentido.

Para impedir que a bola seja rebatida por baixo ou fique presa na quina, nós criamos a classe `Squash` e guardamos a posição vertical do quadro anterior em `anterior_y = self.y`. As posições reais da bola são atualizadas com casas decimais em ponto flutuante: `self.x += self.vx * dt` e `self.y += self.vy * dt`.

Nas três paredes sólidas, a reflexão é direta: se a bola bate na esquerda ou na direita, usamos `abs` para inverter a velocidade horizontal sem risco de inversão dupla. No teto, se `self.y - RAIO < CAMPO.top`, forçamos `self.vy = abs(self.vy)`. A bola tem `RAIO = 11`, começa com `VELOCIDADE_INICIAL = 340` e pode acelerar até `VELOCIDADE_MAXIMA = 680`.

Agora repare no cuidado cirúrgico com a raquete. Nós só aceitamos a colisão se duas condições rigorosas forem satisfeitas juntas:

`cruzou_raquete = (self.vy > 0 and anterior_y + RAIO <= self.raquete.top and self.y + RAIO >= self.raquete.top)`

`sobre_raquete = (self.raquete.left - RAIO <= self.x <= self.raquete.right + RAIO)`

O `cruzou_raquete` exige que a bola esteja descendo, com `self.vy > 0`, e que a borda inferior da bola tenha acabado de atravessar o topo da raquete entre o quadro anterior e o atual. Se ela vier por baixo, a colisão é solenemente ignorada.

Quando a batida é confirmada, colamos a bola imediatamente na face superior com `self.y = self.raquete.top - RAIO`. Depois calculamos o ponto de impacto relativo em `deslocamento = (self.x - self.raquete.centerx) / (self.raquete.width / 2)`, limitamos entre menos um e um, e convertemos esse valor em inclinação com `angulo = math.radians(65 * deslocamento)`. Quanto mais perto da ponta da raquete a bola bater, mais inclinada ela sai. Aceleramos a bola com `self.velocidade = min(VELOCIDADE_MAXIMA, self.velocidade + 14)`, recalculamos os vetores `self.vx` e `self.vy`, somamos `self.rebatidas += 1` e adicionamos dez pontos no placar com `self.pontos += 10`.

Se a bola escapar da raquete e cair pela base da quadra, o teste `if self.y - RAIO > CAMPO.bottom:` apenas zera o movimento e coloca `self.estado = "inicio"`, aguardando um novo saque.

O limite dessa solução é a velocidade máxima. Se você colocasse a bola a três mil pixels por segundo, ela poderia atravessar a raquete inteira em um único quadro, sem que a borda ficasse registrada no intervalo. Mas com o nosso teto de seiscentos e oitenta pixels por segundo, o deslocamento por quadro é de cerca de onze pixels, o que garante detecção perfeita.

Roda aí a Parte 2. Pressiona a barra de espaço para soltar a bola: veja como ela quica nas paredes e como o ângulo de retorno muda conforme você acerta o centro ou as pontas da raquete. Deixa a bola cair uma vez para conferir o reinício. E me diz nos comentários: qual é a importância de verificar `self.vy > 0` antes de aceitar a rebatida na raquete?

A jogabilidade já está divertida, mas a quadra ainda parece um filme mudo. Vamos colocar o primeiro som na Parte 3.

## Parte 3 — Primeiro som

Chegou a hora de dar voz ao jogo. Na Parte 3, nós vamos inicializar o sistema de áudio e tocar os primeiros efeitos nas colisões.

O jeito ingênuo que quase todo mundo tenta na primeira vez é chamar o `pygame.init()`, carregar o arquivo de áudio com `pygame.mixer.Sound` e disparar o efeito sonoro no momento da batida. Aí você roda o jogo, a bola bate na parede e você toma um susto: a imagem da colisão acontece agora, mas o bipe correspondente só chega ao seu ouvido quase meio segundo depois. Essa latência quebra completamente a imersão e faz o jogo parecer lento e mal acabado.

Isso acontece porque, se você não avisar nada antes, o Pygame inicializa o módulo de áudio com configurações padrão conservadoras, alocando um buffer de reprodução enorme, de duas mil ou até quatro mil amostras. Pensa num garçom que só sai da cozinha para atender uma mesa quando a bandeja estiver completamente lotada com dez pratos pesados. Se você pedir um cafezinho rápido, vai ter que esperar ele empilhar pratos alheios até a bandeja encher.

Para resolver esse atraso na raiz, nós precisamos configurar a placa de som antes de qualquer outra coisa no programa, usando esta instrução precisa:

`pygame.mixer.pre_init(44100, -16, 1, 512)`

Essa chamada define a taxa de amostragem em 44100 Hertz, resolução de 16 bits com sinal, um canal mono e, o mais importante de tudo, um tamanho de buffer de apenas 512 amostras. O tamanho da bandeja cai para uma fração mínima, e o atraso entre o evento visual e o som despenca para cerca de dez milissegundos, tornando a resposta instantânea para o cérebro humano.

Depois criamos a classe `Audio`. Ela verifica se o áudio foi inicializado com sucesso através de `pygame.mixer.get_init() is not None`. Se o computador estiver sem dispositivo de som, o jogo não quebra: ele apenas exibe uma mensagem amigável no terminal e continua funcionando silenciosamente.

Carregamos os arquivos dentro de um bloco protegido:

Em um `try` nós fazemos `self.efeitos[nome] = pygame.mixer.Sound(str(caminho))`. Se o arquivo não existir ou o mixer falhar, o `except (FileNotFoundError, pygame.error) as erro:` só imprime o aviso e o jogo segue mudo naquele efeito.

Mapeamos `"parede": "parede.wav"` e `"raquete": "raquete.wav"`. Quando a bola atinge qualquer uma das paredes ou o teto, chamamos `self.audio.tocar("parede")`. E quando bate na raquete, chamamos `self.audio.tocar("raquete")`. O método interno executa o disparo do efeito sem travar o laço principal.

O custo dessa abordagem direta é que tocar com o método padrão do efeito sonoro utiliza qualquer canal livre do mixer. Se duas colisões acontecerem em sequência muito rápida, os efeitos podem se sobrepor de forma desordenada ou cortar um ao outro, sem nenhum controle sobre qual som é mais importante.

Pausa o vídeo e roda aí a Parte 3. Solta a bola e repara no som da parede e no som da raquete: o bipe precisa soar no mesmo instante em que a bola toca a superfície. Testa aí do seu lado e responde nos comentários: por que a chamada do `pygame.mixer.pre_init` precisa acontecer obrigatoriamente antes do `pygame.init()`?

Agora que o som básico está funcionando, vamos resolver a sobreposição de efeitos e o equilíbrio de volume na Parte 4.

## Parte 4 — Canais, volume e mute

Na Parte 4, nós vamos organizar o áudio como profissionais: separar colisões mecânicas de avisos de pontuação em canais independentes, calibrar volumes e criar um botão de mudo.

Olha o problema que acontece se você deixar todos os efeitos sonoros soltos no mesmo canal padrão. As colisões com as paredes acontecem a cada dois segundos. Se o som da parede tiver o mesmo volume e disputar o mesmo canal que um som comemorativo de pontuação, o barulho constante da parede abafa tudo e cansa o ouvido do jogador. Pior ainda: se você pontuar bem no instante em que a bola raspa na quina, o bipe da parede corta o som de ponto pela metade.

Imagina a transmissão de uma partida de futebol na televisão. O narrador tem o microfone principal dele e o estádio tem o microfone de ambiente da torcida. Se o operador de áudio colocar o som dos tambores da torcida no mesmo volume e no mesmo canal da voz do narrador, você não consegue entender nada do que está sendo narrado. Cada elemento precisa do seu canal e do seu nível de ganho calibrado.

No código, nós configuramos o mixer para gerenciar oito canais simultâneos com `pygame.mixer.set_num_channels(8)`. Adicionamos um novo arquivo na tabela de efeitos: `"ponto": "ponto.wav"`. E na hora de tocar, nós separamos os canais e ajustamos os volumes com precisão:

`canal = pygame.mixer.Channel(0 if nome in ("parede", "raquete") else 1)`

`canal.set_volume(0.30 if nome in ("parede", "raquete") else 0.56)`

`canal.play(self.efeitos[nome])`

Olha a elegância dessa separação. O `Channel(0)` fica reservado exclusivamente para os impactos mecânicos repetitivos de parede e raquete, com um volume atenuado de `0.30`. Já o `Channel(1)` fica dedicado para avisos e conquistas, como o som de ponto, com volume destacado em `0.56`. Dessa forma, mesmo que a bola bata na parede no mesmo instante em que você marca pontos, o som de comemoração toca límpido no canal um sem ser interrompido pelo canal zero.

E para criar um bônus dinâmico no jogo, verificamos as rebatidas:

`if self.rebatidas % 5 == 0:`

`    self.pontos += 25`

`    self.audio.tocar("ponto")`

A cada cinco rebatidas completadas com sucesso, o jogador ganha vinte e cinco pontos extras e ouve o som especial de bônus.

Para dar conforto a quem joga, criamos também o controle de mudo na tecla M. O método `alternar()` inverte a variável booleana `self.ativo`. Se o som for desligado durante a partida, chamamos `pygame.mixer.stop()` para cortar qualquer reprodução ativa na hora, e a interface exibe o status no rodapé.

Ah, Elzo, mas não seria melhor criar um canal exclusivo para cada um dos cinco sons do jogo? Na verdade não. Se você criar um canal para cada arquivo, você perde o controle de hierarquia e corre o risco de criar uma cacofonia desgovernada. Agrupar os efeitos por categoria de prioridade, mantendo colisões de fundo de um lado e avisos do jogo do outro, é o padrão clássico e robusto da indústria de jogos.

Roda aí a Parte 4. Rebate a bola cinco vezes seguidas até ouvir o som de bônus tocando alto no canal um por cima da raquete, e aperta a tecla M para silenciar e reativar o áudio. Faz esse teste prático e me explica nos comentários: por que colocamos o volume em `0.30` nas colisões e `0.56` no som de ponto?

Com o áudio equilibrado e profissional, só falta fechar as regras do jogo: adicionar vidas, tela de pausa, perda de bola e encerramento. Vamos para a Parte 5.

## Parte 5 — Vidas, estados e bônus

Na Parte 5, nós montamos o jogo completo: gerenciamento de três vidas, controle de estados de jogo, telas de aviso translúcidas e sons dramáticos de perda de vida e fim de partida.

Aqui acontece um erro muito comum quando quem está começando tenta programar o sistema de vidas. A pessoa cria a variável de vidas e, quando a bola ultrapassa a borda inferior do campo, simplesmente subtrai uma vida com um decremento numérico. Aí você roda a partida, erra a bola uma única vez e, num piscar de olhos, todas as suas vidas somem instantaneamente.

Isso acontece porque o laço principal roda a sessenta quadros por segundo. Se a bola passou da raquete e continua caindo, no quadro seguinte ela continua abaixo da borda inferior. Se você não congelar a física e não alterar o estado da partida imediatamente, o código executa o decremento repetidas vezes em frações de segundo até esgotar tudo.

Pensa no árbitro de uma partida de tênis ou squash. Quando a bola quica duas vezes no chão ou sai da quadra, ele apita na mesma hora e a jogada é interrompida. O jogo fica paralisado aguardando o saque seguinte. O relógio da disputa não pode continuar rolando com a bola perdida nas arquibancadas.

No nosso código, definimos `VIDAS_INICIAIS = 3` e carregamos dois novos efeitos dramáticos: `"vida": "vida.wav"` e `"fim": "fim.wav"`. Quando a bola cruza a linha de fundo em `if self.y - RAIO > CAMPO.bottom:`, nós chamamos o método `self.perder_vida()`:

```python
def perder_vida(self) -> None:
    self.vidas -= 1
    if self.vidas <= 0:
        self.estado = "fim"
        self.audio.tocar("fim")
    else:
        self.estado = "vida_perdida"
        self.audio.tocar("vida")
```

A grande mágica dessa função está na transição de estado. Logo na primeira linha do método `atualizar`, temos a proteção: `if self.estado != "jogando": return`. Quando o estado muda para `"vida_perdida"` ou `"fim"`, a física inteira é paralisada na hora. A bola não anda mais, o teste da borda inferior deixa de ser avaliado e as vidas ficam completamente protegidas.

Para retomar o jogo de forma limpa, criamos o método `iniciar_ou_continuar()`. Se o estado for `"inicio"` ou `"vida_perdida"`, ele posiciona a bola e executa `self.soltar_bola()`. Se o jogo estiver pausado, ele restaura para `"jogando"`. E se a partida tiver chegado ao fim, ele reinicializa todo o placar com `self.zerar()` e solta a bola novamente.

Nos eventos do teclado, a tecla P agora alterna a pausa da partida, a tecla R permite reiniciar o jogo a qualquer momento, e a tecla M continua operando o mudo. No desenho, quando o jogo não está em andamento, criamos uma camada escura semitransparente sobre a quadra e desenhamos caixas com mensagens elegantes: "PREPARE-SE", "PAUSADO", "VOCÊ PERDEU UMA VIDA" e "FIM DE JOGO".

O custo dessa implementação é que estamos usando strings simples para representar os estados do jogo. Para um projeto focado e coeso como o Squash Arcade, isso funciona perfeitamente e mantém a leitura do código muito acessível. Mas vale o aviso: em jogos gigantescos, com dezenas de inventários e fases complexas, o uso de enumerações formais ajuda a evitar erros bobos de digitação no meio do caminho.

Roda aí a Parte 5 e joga uma partida completa. Testa errar a bola para ouvir o som de vida perdida, aperta P para congelar a ação no meio de uma jogada, perde as três vidas para conferir o som de encerramento e aperta R para recomeçar tudo do zero. Deixa aí nos comentários: por que a guarda no início da função de atualização é fundamental para as vidas não sumirem todas de uma vez?

Com isso, o Squash Arcade está pronto, redondo e sonoro. Agora eu quero ver você deixar esse jogo com a sua cara.

## Desafio — sua variação

O jogo base está completo, mas a partir de agora o projeto é seu. O meu desafio é você escolher uma mecânica e implementar a sua própria variação no Squash Arcade.

Aqui vão algumas sugestões bem legais que você pode tentar:

Primeira ideia: fazer o timbre do som da raquete mudar dinamicamente de acordo com a velocidade da bola ou com o ponto em que ela acertou a raquete, usando o valor de `deslocamento`.

Segunda ideia: criar comandos de teclado com as teclas de mais e menos para aumentar e diminuir o volume dos canais de áudio durante a partida, mostrando a barra de volume na interface.

Terceira ideia: adicionar uma música de fundo em reprodução contínua com o módulo de música do Pygame, garantindo que a nossa tecla M silencie tanto os efeitos sonoros quanto a trilha sonora.

Quarta ideia: criar um modo de jogo com raquete retrátil, onde a raquete perde dez pixels de largura a cada bônus de cinco rebatidas que você conquistar.

A única regra do desafio é que a sua modificação precisa alterar uma regra ou mecânica do jogo, e não apenas trocar uma cor na tela. E você precisa conseguir explicar qual trecho de código foi alterado. Escolhe uma dessas ideias, implementa no seu código e depois vem aqui nos comentários me contar o que você fez e qual conceito desta aula você utilizou.

## Fechamento

Lembra dos problemas que nós listamos lá no comecinho do vídeo? O som que saía atrasado, os efeitos que cortavam uns aos outros, as vidas que sumiam em cascata e o volume sem controle no fone de ouvido?

Neste vídeo nós resolvemos cada um deles com código real e conceitos sólidos de arquitetura. Você aprendeu a usar o `pygame.mixer.pre_init` para zerar a latência do áudio, organizou canais dedicados com `Channel(0)` e `Channel(1)` para dar prioridade aos avisos importantes sem interromper as colisões, controlou o mudo com `mixer.stop`, construiu uma máquina de estados finitos consistente e garantiu uma física de rebatidas impecável.

E guarda muito bem esses conceitos de áudio, colisão e gerenciamento de estados, porque no próximo vídeo da nossa trilha nós vamos construir o clássico Breakout! Nós vamos reaproveitar toda a estrutura de game loop, delta time, canais de som e reflexão angular, só que agora destruindo dezenas de tijolos coloridos na tela ao mesmo tempo.

Se este vídeo te ajudou a destravar a programação de jogos com som no Pygame, deixa o seu like e se inscreve no canal para não perder os próximos projetos. Se ficou qualquer dúvida sobre o código ou sobre a configuração do mixer, deixa nos comentários que eu faço questão de responder.

Um grande abraço, bons códigos e até o Breakout!

<!-- ilustrativo
pygame.init() antes do pre_init
Sound.play()
x += 5
0.75
1.5
if bola.colliderect(esquerda): vx = -vx
colliderect
+10
+25
pre_init
init
-->
