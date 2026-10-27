# SPEC — Dino Runner (Pygame-CE, versão de aula)

Endless runner inspirado no dinossauro do Chrome, para aulas. Tudo em **português** (comentários, textos, README).

## Tecnologia
- Python 3 + pygame-ce 2.5.8. Janela 960x540. Sem assets externos: pixel art colorida e minimalista desenhada em código.
- Arquivo único `main.py`, muito comentado em português, organizado em seções que correspondem às 6 etapas abaixo + polimento.
- Usar `pygame.sprite.Sprite`/`Group`, colisões com `pygame.Rect`, `pygame.time.Clock`, movimento com delta time.

## Mecânicas
- Dino em x fixo; mundo rola da direita para a esquerda. Corrida automática após iniciar; animação de corrida 4–6 quadros.
- Pulo: Espaço/Seta para cima (impulso + gravidade), sem pulo duplo, alto o suficiente para cactos.
- Abaixar: Seta para baixo (hitbox mais baixa) para passar sob pterodáctilos.
- Hitboxes levemente menores que os sprites.
- Pontuação proporcional à distância; recorde salvo em arquivo JSON (ao lado do main.py).
- Obstáculos: cacto simples, cactos agrupados, pterodáctilo (várias alturas, animado).
- Gerador controla espaçamento: nunca combinações impossíveis (sempre há espaço para pousar), considerando a velocidade atual.
- Dificuldade: começa em 320 px/s, +8 px/s a cada 10 s, máximo 620 px/s. Início só cactos simples; grupos depois; pterodáctilos mais tarde.
- Cenário: deserto com camadas em parallax (dunas/montanhas), nuvens lentas, chão rolando.
- HUD pequena no canto superior direito (pontos e HI).
- Estados: título (com instruções), jogando, pausa (P/Esc), game over (pontuação, recorde, reiniciar).
- Som (etapa 6): efeitos sintetizados sem numpy (gerar bytes de onda e `pygame.mixer.Sound(buffer=...)`) para pulo, colisão e marco de pontos (a cada 100). Falhar silenciosamente se não houver dispositivo de áudio.
- Polimento: partículas de poeira ao correr/pousar; ciclo dia/noite opcional.
- Nada de power-ups, moedas, armas, múltiplos personagens.

## Etapas (seções do código)
| Etapa | Entrega | Conceitos |
|---|---|---|
| 1 | Dinossauro correndo e pulando | Game loop, eventos, gravidade |
| 2 | Chão e cenário rolando | Coordenadas, delta time, animação |
| 3 | Cactos surgindo | Objetos, aleatoriedade, colisões |
| 4 | Pontuação e game over | Condicionais, estados, persistência |
| 5 | Pterodáctilos e agachar | Herança/composição, hitboxes |
| 6 | Música, efeitos e polimento | Áudio, recursos, arquitetura |

## Modo demo
`python3 main.py --demo`: piloto automático que pula/abaixa sozinho ao detectar obstáculos. Salva capturas em `prints/` (`titulo.png`, `jogo.png`, `gameover.png`) — com driver dummy deve percorrer título → jogo → game over (pode forçar colisão após alguns segundos) e sair sozinho em < 12 s.

## Entregáveis
`main.py`, `README.md` (pt-BR: como rodar, controles, conceitos por etapa, tabela das 6 etapas), `requirements.txt` (`pygame-ce`).

## Aceitação
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 15 python3 main.py --demo` termina sem exceções (exit 0) e cria os 3 prints.

## Adendo — tema "clássico" (referência Chrome dino)
- Novo tema "clássico": fundo branco, T-rex pixel art cinza-escuro (#535353), cactos saguaro (simples e grupos de 2–3 de tamanhos diferentes), nuvens pixel com contorno claro, chão como linha fina com pequenas saliências e pontinhos espalhados.
- Alternar com tecla T na tela de título e flag `--classico`. O tema colorido (deserto com parallax) continua como o outro tema.
- Em AMBOS os temas: sprite do dino segue a silhueta do T-rex do Chrome; HUD no canto superior direito no formato `HI 000849  000660` (dígitos com zeros à esquerda, fonte pixel em negrito).
- No `--demo`, salvar também `prints/classico.png` (aceitação passa a exigir 4 prints).
