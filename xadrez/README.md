# Xadrez

Jogo de xadrez didático em **Python + Pygame** (pygame-ce). Um único `main.py`, peças desenhadas com polígonos, tabuleiro estilo chess.com. Feito para as aulas do Elzo.

## Como rodar

```bash
cd ~/desenvolvimento/jogos/xadrez
python3 main.py
```

Modo demonstração (IA vs IA + screenshots em `prints/`):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 main.py --demo
```

Teste de geração de lances (perft):

```bash
python3 main.py --perft 3   # esperado: 8902
```

## Controles

| Entrada | Ação |
|---------|------|
| Clique | Selecionar casa / mover |
| 1 | Modo 2 jogadores |
| 2 | Você de Brancas vs IA |
| 3 | Você de Pretas vs IA |
| R | Reiniciar |
| ESC | Sair |

## O que tem no jogo

- Tabuleiro creme/verde com rótulos A–H e 1–8
- Destaque da casa selecionada e dos lances legais
- Regras: roque, en passant, promoção (sempre a rainha na UI), xeque, xeque-mate, afogamento
- IA: minimax com poda alfa-beta, profundidade 2
- Modo `--demo` grava `prints/inicio.png`, `meio.png`, `fim.png`

## Conceitos usados em aula

- Representação de tabuleiro (matriz 8×8)
- Geração de lances e filtragem por legalidade (rei em xeque)
- Recursão (`perft`) para validar o motor
- Minimax + alfa-beta
- Eventos de mouse/teclado no Pygame
