# Pac-Man

Clone didático de Pac-Man em **Python + Pygame** (pygame-ce). Um único `main.py`, labirinto azul, 4 fantasmas com modos chase/scatter/frightened. Feito para as aulas do Elzo.

## Como rodar

```bash
cd ~/desenvolvimento/jogos/pac-man
python3 main.py
```

Demo (auto-piloto + screenshots):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 main.py --demo
```

## Controles

| Tecla | Ação |
|-------|------|
| Setas | Mover Pac-Man |
| R | Reiniciar |
| ESC | Sair |

## O que tem no jogo

- Labirinto azul em fundo preto, túneis laterais
- Bolinhas brancas e power pellets nos cantos
- Pac-Man amarelo com “bocada” animada
- Fantasmas vermelho / rosa / ciano / laranja
- Modos: scatter, chase, frightened (após power), olhos (volta à casa)
- Casa dos fantasmas com porta branca
- Score e vidas no rodapé

## Conceitos usados em aula

- Tilemap / grid
- Máquina de estados simples (modos dos fantasmas)
- Path choice greedy (menor distância ao alvo)
- Colisão por proximidade
- Game loop com `dt`
