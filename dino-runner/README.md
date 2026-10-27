# Dino Runner (Pygame-CE — Versão de Aula)

Jogo estilo *endless runner* inspirado no clássico dinossauro do Chrome, desenvolvido inteiramente em **Python 3** com **pygame-ce** em um único arquivo (`main.py`), sem dependência de arquivos externos de imagem, fonte ou som. Toda a arte em pixel art (T-Rex animado em 6 quadros seguindo a silhueta do Chrome, cactos saguaro simples e agrupados de 2–3 tamanhos, pterodáctilos animados, nuvens contornadas, deserto em parallax com dunas e montanhas, ciclo dia/noite e partículas de poeira), a fonte bitmap em negrito da HUD (`HI 000849  000660`) e todos os efeitos sonoros são gerados diretamente via código.

O jogo conta com **dois temas visuais** alternáveis a qualquer momento:
- **Tema Deserto Colorido (padrão)**: céu com ciclo dia/noite, montanhas e dunas em parallax, T-Rex verde e cactos/pterodáctilos coloridos.
- **Tema Clássico (referência Chrome Dino)**: fundo branco (`#FFFFFF`), T-Rex e obstáculos em cinza-escuro (`#535353`), cactos saguaro, nuvens pixeladas com contorno claro e chão como linha fina com pequenas saliências e pontinhos espalhados.

---

## Como Rodar

### Pré-requisitos
Instale a dependência listada em `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Executar o jogo normal (Tema Colorido padrão)
```bash
python3 main.py
```

### Executar iniciando diretamente no Tema Clássico (Chrome Dino)
```bash
python3 main.py --classico
```

### Executar o modo demonstração (Piloto Automático + 4 Capturas de Prints)
```bash
python3 main.py --demo
```
No modo `--demo`, o jogo percorre automaticamente as telas de **Título → Jogo (Tema Colorido e Tema Clássico com IA que pula cactos e se abaixa sob pterodáctilos) → Game Over**, salvando 4 capturas de tela em `prints/`:
- `prints/titulo.png`
- `prints/jogo.png`
- `prints/classico.png`
- `prints/gameover.png`

e encerrando sozinho em menos de 12 segundos.

Para rodar o comando de aceitação em ambiente headless (sem monitor ou dispositivo de som):
```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 15 python3 main.py --demo
```

---

## Controles

| Tecla | Ação |
|---|---|
| `Espaço` ou `Seta para Cima (↑)` | Iniciar partida (no título) / Pular (durante o jogo) / Reiniciar (no Game Over) |
| `Seta para Baixo (↓)` | Abaixar / Agachar (reduz a hitbox para passar sob pterodáctilos; acelera queda no ar) |
| `T` | Alternar entre o **Tema Deserto Colorido** e o **Tema Clássico (Chrome `#535353`)** |
| `P` ou `Esc` | Pausar / Retomar a partida (ou sair no Título/Game Over) |
| `R` ou `Enter` | Reiniciar partida na tela de Game Over |

---

## Tabela das 6 Etapas Pedagógicas

O código de `main.py` está estruturado didaticamente em **6 seções numeradas** (mais polimento e temas), permitindo evoluir o projeto passo a passo em sala de aula:

| Etapa | Entrega | Conceitos |
|---|---|---|
| **1** | Dinossauro correndo e pulando | Game loop, eventos, gravidade |
| **2** | Chão e cenário rolando | Coordenadas, delta time, animação |
| **3** | Cactos surgindo | Objetos, aleatoriedade, colisões |
| **4** | Pontuação e game over | Condicionais, estados, persistência |
| **5** | Pterodáctilos e agachar | Herança/composição, hitboxes |
| **6** | Música, efeitos e polimento | Áudio, recursos, arquitetura |

---

## Conceitos por Etapa

1. **Etapa 1 — Dinossauro correndo e pulando (`Game loop, eventos, gravidade`)**:
   - Uso de `pygame.sprite.Sprite` e `pygame.time.Clock` para manter a taxa de quadros estável.
   - Física vertical baseada em `delta time` (`dt`): aplicação de impulso negativo no eixo Y ao pular e aceleração gravitacional contínua até tocar o solo, impedindo pulo duplo.
   - Silhueta do T-Rex do Chrome desenhada em matrizes de pixel art com animação de corrida em 6 quadros.

2. **Etapa 2 — Chão e cenário rolando (`Coordenadas, delta time, animação`)**:
   - O T-Rex permanece em posição `X` fixa enquanto o mundo se move da direita para a esquerda com velocidade em pixels por segundo (`velocidade * dt`).
   - Suporte a dois estilos de cenário: **Deserto em Parallax** (sol/lua/estrelas, montanhas distantes, dunas intermediárias, nuvens e solo colorido) e **Clássico Chrome** (fundo branco, nuvens com contorno claro e linha fina no solo com pequenas saliências e pontinhos espalhados).

3. **Etapa 3 — Cactos surgindo (`Objetos, aleatoriedade, colisões`)**:
   - Criação de obstáculos (`CactoSimples` saguaro e `GrupoCactos` com 2–3 cactos saguaro de tamanhos diferentes) gerenciados por `pygame.sprite.Group`.
   - Gerador inteligente que calcula a distância segura de pouso em função da velocidade atual, garantindo que nunca surjam combinações impossíveis.
   - Progressão gradual de dificuldade: começa em `320 px/s`, aumenta `+8 px/s` a cada `10 s` até o limite de `620 px/s`.

4. **Etapa 4 — Pontuação e game over (`Condicionais, estados, persistência`)**:
   - Máquina de estados clara: `TITULO`, `JOGANDO`, `PAUSA` e `GAMEOVER`.
   - Pontuação proporcional à distância percorrida e HUD no canto superior direito no formato `HI 000849  000660` (6 dígitos com zeros à esquerda, renderizados em fonte pixel em negrito).
   - Persistência do recorde em arquivo JSON (`recorde.json`) ao lado do `main.py`.

5. **Etapa 5 — Pterodáctilos e agachar (`Herança/composição, hitboxes`)**:
   - Hierarquia de obstáculos compartilhando a classe base `Obstaculo(pygame.sprite.Sprite)`.
   - `Pterodactilo` com animação de bater de asas e três faixas de altitude (`baixo`, `medio` e `alto`).
   - Hitboxes reduzidas (`pygame.Rect.inflate`) levemente menores que os sprites visuais e ajuste imediato da caixa de colisão quando o T-Rex se abaixa.

6. **Etapa 6 — Música, efeitos e polimento (`Áudio, recursos, arquitetura`)**:
   - Síntese de ondas sonoras PCM 16-bit em memória (sem `numpy`, usando apenas `math` e `struct`) carregadas com `pygame.mixer.Sound(buffer=...)` para pulo, colisão e marco de 100 pontos, falhando silenciosamente caso não haja dispositivo de áudio.
   - Sistema de partículas de poeira ao correr e pousar, ciclo dia/noite e alternância em tempo real entre os temas Colorido e Clássico (`T` / `--classico`).
