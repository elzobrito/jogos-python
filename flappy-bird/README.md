# Flappy Bird

Clone didático de Flappy Bird em **Python + Pygame** (pygame-ce). Um único `main.py`, pássaro, canos verdes e chão rolante. Feito para as aulas do Elzo.

## Como rodar

```bash
cd ~/desenvolvimento/jogos/flappy-bird
python3 main.py
```

Demo (auto-flap + screenshots):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 main.py --demo
```

## Controles

| Entrada | Ação |
|---------|------|
| Espaço / clique | Flap (bater asas) |
| R ou Espaço (após game over) | Reiniciar |
| ESC | Sair |

## O que tem no jogo

- Pássaro amarelo com asa e bico (polígonos/elipses)
- Canos verdes com vão aleatório
- Chão rolante
- Score ao passar canos
- Game over + restart

## Conceitos usados em aula

- Física simples (gravidade + impulso)
- Scroll infinito / object pooling de canos
- Colisão AABB (`Rect.colliderect`)
- Loop de jogo e eventos
