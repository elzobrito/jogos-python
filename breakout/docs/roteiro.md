# Roteiro falado — Breakout em Python com Pygame: tijolos, colisões e sua própria versão

## Abertura

Você já tem uma raquete, uma bola e uma rebatida funcionando no Pong. Aí resolve colocar uma parede de tijolos na frente dessa bola. Parece uma mudança pequena: desenha os blocos, detecta a batida e manda a bola voltar. Mas olha o que acontece quando ela pega um tijolo pela lateral: se eu inverter só o movimento vertical, ela continua avançando para o mesmo lado. A resposta parece certa numa batida de cima e errada numa batida de lado.

Hoje eu vou construir o Breakout em cinco partes executáveis. Primeiro eu reaproveito a base do Pong, depois monto a grade, faço os tijolos quebrarem e acrescento vidas, vitória e reinício. No final, o lugar onde você acerta a bola com a raquete vai mudar a direção da rebatida, e alguns tijolos vão resistir ao primeiro impacto.

Eu quero mostrar o problema antes de escrever a solução. Assim, quando aparecer uma comparação de sobreposição ou uma variável de estado, você vai saber qual comportamento ela está resolvendo. E depois você vai escolher uma regra para transformar esse Breakout na sua própria versão. Vou começar pela tela do jogo e voltar à primeira parte para construir esse caminho com você.

## O que você precisa

Para acompanhar, você precisa de Python 3, Pygame e um editor. Eu começo conferindo a instalação com `python -c "import pygame"`. Se a biblioteca estiver faltando nesse ambiente, a instrução do material é `pip install pygame`; depois eu repito a conferência. Não vou usar imagens, sons ou fontes baixadas: o desenho e o texto vêm do próprio Pygame.

Cada parte tem seu próprio `main.py` e roda sozinha. Eu vou deixar o acesso às cinco pastas na descrição; se você perder uma alteração, pode retomar a partir da parte correspondente. Abra a primeira e rode `python main.py`. Deixe também espaço para testar o jogo entre as mudanças, porque ver a bola se comportando faz parte da explicação.

## Parte 1 — Base do Pong

O primeiro problema é decidir o que realmente muda quando eu saio do Pong. Se eu começar reescrevendo toda a janela, todo o teclado e todo o movimento, vou gastar tempo reconstruindo coisas que já estavam funcionando. É como mudar a disposição dos móveis: eu preciso pensar no novo uso do espaço antes de sair trocando tudo de lugar. Aqui eu preservo a estrutura do jogo e reorganizo a raquete e as regras das bordas.

A janela agora tem 800 por 600 pixels. A raquete fica embaixo, tem 120 de largura e 14 de altura, e anda para a esquerda e para a direita. A bola continua sendo representada por um `pygame.Rect`, embora apareça redonda no desenho. Essa distinção interessa: o formato que você vê é uma elipse, mas os testes de colisão usam o retângulo.

O relógio aparece em `dt = relogio.tick(FPS) / 1000`. Eu uso o tempo transcorrido para calcular o deslocamento. A posição da bola fica em `bx` e `by`, com casas decimais, e só depois vai arredondada para `bola.topleft`. Pensa numa conta que acumula centavos: se eu jogar fora a parte pequena a cada operação, o total começa a se afastar do esperado. Guardar a posição decimal evita perder esses pedacinhos de movimento a cada quadro.

Para a raquete, `pygame.key.get_pressed()` consulta as setas mantidas pressionadas. Depois, `raquete.clamp_ip(tela.get_rect())` mantém o retângulo dentro da tela. Aqui o deslocamento da raquete é convertido com `int(VEL_RAQUETE * dt)`, então ainda há um arredondamento por quadro nesse objeto. Eu não vou dizer que os dois movimentos têm precisão idêntica: a bola acumula as frações, a raquete usa uma simplificação.

Agora acompanhe as bordas. Nas laterais eu inverto `vx`; no teto eu faço `vy` apontar para baixo. Na raquete, a condição `and vy > 0` limita a rebatida à bola que está descendo, e eu corrijo `by` para colocá-la acima da raquete. Embaixo não existe uma parede: quando a bola sai completamente, `lancar_bola()` prepara outro lançamento. Por enquanto, isso não custa uma vida.

Ah, Elzo, então posso copiar a base e esquecer como ela funciona? Eu preciso entender pelo menos onde ficam o movimento, a colisão e o desenho. Uma correção herdada sem compreensão pode virar um problema no jogo seguinte. Outro limite é que corrigir `bx` ou `by` não atualiza imediatamente o retângulo já usado naquele quadro; ele recebe a nova posição na próxima atualização. Essa versão é curta para acompanhar, mas não é uma simulação física completa.

Roda aí e segura cada seta até a borda. Depois deixe a bola bater no teto, nas laterais e na raquete, e também deixe cair uma vez. Você deve ver o lançamento recomeçar. Qual borda deixou de rebater a bola e passou a representar uma perda? Com essa diferença clara, eu posso preencher o espaço de cima com os tijolos.

## Parte 2 — Grade de tijolos

Um tijolo é fácil de posicionar. Cinquenta posições escritas à mão já são outra história: basta errar o começo de uma linha para a parede ficar torta ou sair da tela. Eu vou tratar a grade como as cadeiras de uma sala: escolho a posição da primeira, a distância entre elas e a quantidade de fileiras. No código, isso vira uma conta inicial e dois laços.

A função `criar_tijolos()` cria uma lista. Cada elemento guarda um retângulo e uma cor, usando as chaves `"rect"` e `"cor"`. O laço externo percorre as linhas, e o interno percorre as colunas. A coordenada horizontal depende da coluna; a vertical depende da linha. Assim, mudar o espaçamento não exige procurar cinquenta posições diferentes.

Antes de montar os retângulos, eu calculo `x0`. A largura total precisa incluir todos os tijolos e somente os espaços que existem entre eles. Com dez colunas, são nove intervalos. A expressão `COLUNAS * TIJ_L + (COLUNAS - 1) * ESPACO` faz essa soma; o restante da largura da janela é dividido entre os dois lados. Eu vou mostrar essa conta na tela antes de rodar, porque um intervalo a mais já desloca a grade.

As cores vêm de `CORES_LINHAS[lin]`. Como o código tem cinco cores para cinco linhas, eu não posso aumentar livremente a quantidade de linhas sem cuidar dessa lista. A fórmula resolve o posicionamento, mas não garante que qualquer configuração caiba na janela ou tenha uma cor disponível. É esse tipo de relação que vale conferir quando você experimenta com as constantes.

Depois que `tijolos = criar_tijolos()` monta a coleção, o desenho percorre seus elementos e chama `pygame.draw.rect`. Eu continuo limpando o fundo e redesenhando a cena a cada quadro. Neste ponto os blocos aparecem, mas ainda não participam da resposta de colisão. Se a bola passar por eles, você não perdeu uma linha escondida: essa regra entra na próxima parte.

O custo dessa solução é manter as informações em dicionários. Para retângulo e cor, fica fácil de ler. À medida que eu acrescentar resistência e outras regras, preciso cuidar para os elementos terem as informações que o restante do jogo espera. Não preciso resolver toda a organização de um jogo maior agora; preciso reconhecer o limite da estrutura que escolhi.

Pausa o vídeo e roda aí. Você deve ver dez colunas e cinco linhas, formando uma grade colorida centralizada. Se a parede ficou deslocada, volte à largura total e ao cálculo de `x0`. Por que a conta dos espaços usa uma unidade a menos que a quantidade de colunas? Quando você conseguir explicar isso, está pronto para fazer essa coleção mudar durante a partida.

## Parte 3 — Quebrar tijolos

Chegou a situação da abertura: a bola encontrou um bloco, mas para onde ela deve voltar? A resposta mais rápida seria usar `vy = -vy` em toda batida. Isso serve para visualizar uma rebatida vertical, mas imagine uma pessoa entrando numa sala pela porta lateral: mandar essa pessoa subir ou descer não desfaz o avanço pela porta. Na bola, eu preciso distinguir o eixo horizontal do vertical.

Vou mostrar o erro com uma colisão lateral controlada. A bola está avançando para a direita, e eu inverto apenas `vy`. Ela muda o sentido vertical, mas `vx` continua positivo. Dependendo da trajetória, pode alcançar outros tijolos em quadros seguintes. Eu não vou prometer que vários desapareçam de uma vez: neste código existe uma única seleção de tijolo por quadro. O defeito que eu quero que você observe é a direção horizontal que não foi corrigida.

A detecção começa com `bola.collidelist([t["rect"] for t in tijolos])`. Eu preparo uma lista dos retângulos e recebo o índice do primeiro que se sobrepõe à bola. Quando não há colisão, o resultado é menos um. Quando há, uso esse índice para acessar o elemento correspondente na coleção original. Detecção e resposta continuam sendo decisões diferentes: encontrar o tijolo não informa sozinho como rebater.

A resposta fica em `rebater_no_tijolo`. Dentro dela, `sobre_x` e `sobre_y` medem as menores sobreposições em cada eixo. Pensa em duas caixas parcialmente encaixadas: eu procuro o caminho mais curto para separá-las. Se a sobreposição horizontal for menor, trato como batida lateral, inverto `vx` e ajusto `bx`. Caso contrário, inverto `vy` e ajusto `by`. O retângulo da bola vai receber essa posição corrigida na próxima atualização.

Repare no limite dessa escolha. Eu estou inferindo o lado pela geometria do quadro atual; não estou reconstruindo todo o caminho que a bola percorreu. Uma quina pode deixar a decisão ambígua e, em caso de igualdade, o código segue o ramo vertical. Ah, mas isso resolve qualquer velocidade e qualquer colisão? Não. É uma resposta simples por menor sobreposição, adequada para estudar essa regra, sem garantia de resolver todos os encontros possíveis.

Depois da resposta, `tijolos.pop(i)` remove o elemento e `pontos += 10` atualiza o placar. Eu não estou percorrendo a própria coleção com um laço e removendo itens no meio desse percurso. Pensa numa lista de lugares numerados: quando você tira um elemento, os seguintes mudam de posição. Aqui eu obtenho um índice, trato um encontro e removo uma vez, evitando depender de uma sequência de índices durante a remoção.

Agora roda aí e observe uma batida de cima e outra de lado. O tijolo atingido deve desaparecer, o placar deve subir e a direção deve mudar conforme o eixo escolhido. Para investigar o bug, substitua temporariamente a chamada de resposta pela inversão vertical, compare uma batida lateral e restaure o código. Se a bola estava indo para a direita, por que mudar apenas `vy` não a manda para a esquerda? Essa pergunta é o centro desta parte. Em seguida, vou dar consequência às quedas que até agora eram gratuitas.

## Parte 4 — Vidas e estados

Quebrar os tijolos já funciona, mas eu ainda posso perder a bola indefinidamente. E, se apenas escrever uma mensagem de fim sem mudar a atualização, o jogo continua acontecendo atrás dela. Pensa num semáforo: a luz precisa orientar o que os carros podem fazer; não basta existir uma placa colorida. Aqui a variável `estado` vai decidir se o mundo ainda deve se mover.

Eu começo com `vidas = 3` e `estado = "JOGANDO"`. O bloco de movimento, que antes estava sob `if True:`, passa a depender de `if estado == "JOGANDO":`. Isso reúne a atualização da raquete, da bola e das colisões sob uma condição. Já a leitura dos eventos e o desenho continuam fora desse bloco, porque eu ainda preciso fechar a janela e mostrar o resultado quando a partida terminar.

Quando `bola.top > ALTURA`, a bola já passou completamente pela borda inferior. Eu diminuo uma vida e, se o total chegou a zero, atribuo `"GAME_OVER"`. O código ainda chama `lancar_bola()` nessa queda, mas, a partir da próxima volta do laço, o bloco de movimento fica desativado pelo estado. É uma diferença de ordem que eu quero deixar clara: alterar a variável não interrompe automaticamente as instruções restantes daquela volta.

A vitória usa a própria coleção como evidência: `if not tijolos:` significa que a lista ficou vazia. Nesse caso, o estado recebe `"VITORIA"`. No desenho, o código escolhe entre a mensagem de vitória e a de fim de jogo, e mostra a indicação para jogar novamente. Eu não preciso manter um contador separado de tijolos destruídos para reconhecer que a parede acabou.

O reinício vem de um evento de tecla, com `pygame.KEYDOWN`, e só é aceito quando o estado já não é de partida em andamento. A função `reiniciar()` recria os tijolos, zera os pontos, recupera as três vidas e libera a atualização, além de lançar a bola. Ela preserva a posição horizontal atual da raquete. Então, ao demonstrar, eu não vou dizer que todos os objetos voltam para a posição inicial: vou mostrar exatamente o que essa função restaura.

Essa variável funciona como o semáforo que combinamos no começo: o mesmo laço continua vivo, mas algumas ações deixam de ser permitidas. Se eu acrescentasse muitos modos, telas e transições, teria mais relações para organizar. Por enquanto são três situações, e a condição no começo do bloco deixa visível por que o movimento para.

Roda aí e deixe as três bolas caírem. Confira a mensagem, aperte R e veja a partida voltar; durante uma partida ativa, essa tecla não deve reiniciar. Para a vitória, acompanhe a remoção dos tijolos até a lista esvaziar. Qual parte continua funcionando mesmo com o movimento parado, e por que isso permite reiniciar? Agora vou mexer na rebatida para você escolher melhor a direção da bola.

## Parte 5 — Ângulo e variação

Se eu só trocar a cor da parede, vou ter uma aparência diferente com a mesma decisão de jogo. Eu quero dar ao jogador uma escolha durante a rebatida e mudar a regra de alguns tijolos. Imagine uma régua sobre a raquete: o centro é a referência, e cada lado indica um desvio. No código, a diferença entre os centros da bola e da raquete vai orientar a nova velocidade horizontal.

A conta fica em `desvio = (bola.centerx - raquete.centerx) / (raquete.width / 2)`. Um impacto à esquerda do centro produz desvio negativo; à direita, positivo. Em seguida, `vx = vel * 0.85 * desvio` transforma essa posição em movimento horizontal. Bem no centro, a componente horizontal calculada fica zero. Isso não exige uma tecla de mira: você escolhe onde posicionar a raquete antes do encontro.

O movimento vertical é calculado com `vy = -((vel * vel - vx * vx) ** 0.5)`. Eu quero que a bola saia subindo e que as duas componentes componham a velocidade escolhida. Vou mostrar os impactos no meio e nos lados, sem vender isso como uma reprodução de física real. É uma regra de controle que liga o posicionamento da raquete ao resultado da jogada.

Também existe uma aceleração: a conta de `vel` multiplica a velocidade atual por 1,02 e usa `min` para limitar o resultado a `VEL_BOLA * 1.8`. Esse ajuste acontece quando a bola rebate na raquete, não em toda batida num tijolo. Pensa num acelerador com limitador: eu deixo a troca ficar mais rápida, mas paro de aumentar ao alcançar o teto. Ainda preciso avaliar o efeito no jogo; colocar um limite não garante, sozinho, que qualquer configuração fique fácil ou justa.

A outra mudança está na criação dos tijolos. Agora cada dicionário também guarda `"vida"`: a primeira linha começa com duas, as outras com uma. Ao colidir, `tijolos[i]["vida"] -= 1` reduz a resistência. Só quando ela chega a zero eu removo o elemento. Enquanto ainda tem mais de uma vida, o desenho coloca um contorno claro, dando uma pista visual da regra que mudou.

Olhe também a pontuação real desta parte, porque ela mudou junto. Existe um acréscimo de dez pontos no impacto e outro de dez quando o tijolo é removido. Um tijolo comum rende vinte ao quebrar. O resistente rende dez na primeira batida e vinte na segunda, totalizando trinta. Se eu continuar dizendo que todo tijolo vale dez, vou descrever a versão anterior, e você vai olhar o placar sem entender o salto.

O custo é que já estamos combinando geometria, velocidade, resistência e pontos no mesmo programa. Cada nova regra precisa conversar com as anteriores. Além disso, o desvio é calculado pela diferença dos centros durante uma sobreposição, então não vou tratar o comentário de menos um a um como uma trava explícita: o código não faz esse recorte. O importante para o teste proposto é observar o sinal e a mudança da direção.

Pausa e roda aí. Acerte a bola perto do meio e depois em cada lado da raquete. Tente alcançar a primeira fileira e veja o tijolo resistir ao primeiro impacto, perder o contorno e quebrar no seguinte. Que decisão sua mudou a trajetória, e que informação do tijolo passou a decidir sua remoção? Com essas duas respostas, você já tem exemplos de mudanças de mecânica para criar a sua.

## Desafio — sua variação

Agora eu quero que você escolha uma regra e a aplique no seu Breakout. Pode fazer um tijolo soltar um bônus que aumenta a raquete, ou criar outra fase com uma grade diferente depois da vitória. Também pode experimentar um placar de recorde durante a sessão. Você não precisa juntar todas as ideias: escolha uma e consiga explicar o efeito dela.

Outra opção do material é o tijolo indestrutível. Antes de implementar, observe a relação com a vitória: se esse objeto continuar na lista, a lista não fica vazia. Você precisa decidir como reconhecer o fim da fase com essa nova regra. Isso é parte da variação, não um comportamento que já está resolvido na versão que acabamos de construir.

Se preferir desenhar um nível próprio, pense em como a disposição dos blocos muda a trajetória e a dificuldade. Mudar somente a cor não atende ao desafio. Eu quero uma mudança de regra ou mecânica que rode, e uma explicação do trecho alterado. Conte nos comentários o que você escolheu e qual conceito usou: coleção, colisão, estado ou controle da rebatida. A explicação ajuda a conferir se você sabe por que a mudança funcionou.

## Fechamento

Volta à batida lateral da abertura. Agora você sabe por que inverter apenas o movimento vertical deixa o avanço horizontal sem resposta, e como a menor sobreposição orienta o eixo da rebatida nesta versão. Você também viu a mesma coleção servir para desenhar, encontrar uma colisão, remover um tijolo e reconhecer a vitória.

Eu saí da base do Pong e cheguei a um Breakout com grade, pontuação, vidas, reinício, controle pela raquete e tijolos resistentes. Na sequência da trilha vem Space Invaders, e essa prática com uma coleção de objetos vai ser reaproveitada. Antes disso, teste a sua variação e tente explicar a regra sem depender de ler o programa inteiro.

Se o vídeo ajudou você a entender essas decisões, deixe o like e se inscreva para acompanhar a sequência. Se ficou uma dúvida, escreva nos comentários qual parte você estava testando e o que aconteceu. Um abraço, e até o próximo vídeo.

<!-- ilustrativo
main.py
-->
