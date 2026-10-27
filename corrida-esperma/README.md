# Corrida de Espermatozoides

Protótipo didático em **Python + Pygame**: corrida **pseudo-3D** (estilo OutRun / Top Gear) com 80 espermatozoides fofos num túnel rosado. Feito para as aulas do Elzo — um único `main.py`, só primitivas, comentado em português.

## Como rodar

Requisito: **pygame-ce** no Python do sistema (3.14). No notebook do Elzo já está instalado globalmente com:

```bash
python3 -m pip install --user --break-system-packages pygame-ce
```

(`pygame` clássico ainda não tem wheel para 3.14; use `pygame-ce`, que exporta o mesmo `import pygame`.)

```bash
cd ~/desenvolvimento/jogos/corrida-esperma
python3 main.py
```

Modo demonstração (autoplay + screenshots em `prints/`):

```bash
SDL_VIDEODRIVER=dummy python3 main.py --demo
```

Janela: **1024×576** · **60 FPS**.

## Controles

| Tecla | Ação |
|-------|------|
| ← → / A D | Mover na pista |
| Espaço | Turbo (gasta energia) |
| P | Pausa (Resume / Sound on/off / Restart) |
| R | Reiniciar do começo |
| ESC | Sair |

## O que tem no jogo

- Pista em perspectiva com faixas rosadas, curvas e zebras laterais
- Jogador fixo embaixo (vista de trás); rivais escalados pela distância
- HUD: posição (`Nº / 80`), velocímetro em `mm/s`, energia/turbo, barra até o óvulo + minimapa
- Contagem 3-2-1-GO, glóbulos que empurram, faixa quadriculada e óvulo na meta
- Vitória: *“Parabéns, você existe!”* · Derrota: *“Você chegou em Nº… tente outra vida”*

Sem assets externos: tudo com círculos, elipses, polígonos e caudas senoidais.
