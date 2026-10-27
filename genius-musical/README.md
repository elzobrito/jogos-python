# Genius Musical — Memória Visual e Musical

O **Genius Musical** é um jogo de memória audiovisual no estilo *Simon*, desenvolvido em Python com Pygame-CE. O jogador acompanha e reproduz sequências sonoras e visuais crescentes associadas a quatro elementos da natureza: **Fogo**, **Água**, **Terra** e **Ar**.

A cada rodada vencida, o jogo mantém a sequência anterior e adiciona uma nova nota, desafiando a memória do jogador.

---

## 🎯 Conceitos Pedagógicos Ensinados

Este projeto foi desenhado como material didático prático após os projetos *Pong* e *Squash Arcade*, preparando a base para *Breakout* e *Tetris*. Os principais conceitos explorados são:

1. **Manipulação e Renderização de Sprites**:
   - `pygame.image.load()`: carregamento seguro de recursos visuais externos.
   - `.convert_alpha()`: conversão de superfície para o formato de pixel do display preservando canal alfa (transparência).
   - `pygame.transform.smoothscale()`: redimensionamento bilinear de alta fidelidade para ícones vetoriais/rasterizados.
   - `Surface.blit()`: composição em camadas (fundo → cartão geométrico → ícone PNG → texto).

2. **Geometria de Interface e Retângulos Clicáveis**:
   - Utilização de `pygame.Rect` para delimitar regiões disjuntas em grade 2×2.
   - Algoritmo de *hit-testing* (`rect.collidepoint(pos)`) para mapear cliques do mouse de forma independente da resolução do sprite.
   - Distinção clara entre o sprite (PNG transparente) e a geometria do botão desenhada com `pygame.draw.rect` e cantos arredondados (`border_radius`).

3. **Síntese de Áudio Digital em Memória (PCM Senoidal)**:
   - Geração procedural de som puro sem necessidade de arquivos externos `.wav` ou `.mp3`.
   - Amostragem PCM mono 16-bit com `array('h')` a 44.100 Hz.
   - Cálculo amostra a amostra da função senoidal:  
     $$s[n] = A \cdot \sin\left(2\pi f \frac{n}{F_s}\right)$$
   - Aplicação de envelope linear curto de ataque (~10 ms) e relaxamento (~30 ms) para eliminar cliques/estalos na descontinuidade do sinal.
   - Instanciação de `pygame.mixer.Sound(buffer=...)` reutilizando buffers alocados uma única vez na inicialização.
   - Resiliência contra ausência de placa de som (*graceful fallback* com `disponivel=False`), permitindo jogar em modo exclusivamente visual.

4. **Máquina de Estados Finita (FSM) e Delta Time (`dt`)**:
   - Estados bem definidos: `MENU`, `DEMONSTRANDO`, `ENTRADA`, `FEEDBACK`, `FIM`, `PAUSADO`.
   - Temporizadores contínuos baseados em `dt` (segundos reais), garantindo taxa de quadros estável (60 FPS) e evitando bloqueios por `time.sleep()`.
   - Bloqueio de entradas indevidas durante a fase de demonstração da sequência.

5. **Arquitetura Desacoplada e Testável**:
   - `jogo.py`: regras puras do jogo, permitindo testes unitários headless com `pytest`.
   - `audio.py`: camada isolada de síntese e reprodução sonora.
   - `interface.py`: renderização visual e mapeamento de componentes gráficos.
   - `configuracao.py`: centralização de constantes (cores, frequências, tempos, caminhos).
   - `main.py`: ciclo de vida da aplicação e despacho de eventos.

---

## 🎬 Aula em vídeo

- Roteiro falado: [`docs/roteiro.md`](docs/roteiro.md)
- Código passo a passo (5 partes executáveis) em [`partes/`](partes/):
  1. `parte-01-tela-imagens` — janela e sprites PNG (`image.load`, `convert_alpha`, `smoothscale`, `blit`)
  2. `parte-02-cliques-teclas` — retângulos clicáveis e teclas 1–4
  3. `parte-03-sequencia-estados` — sequência crescente e máquina de estados com `dt`
  4. `parte-04-notas-sintetizadas` — síntese PCM senoidal (`array('h')`, envelope, `Sound(buffer=...)`)
  5. `parte-05-sincronizacao-completa` — sincronização, pausa e mute (jogo completo)

Cada parte roda sozinha: `cd partes/parte-0X-... && python3 main.py`.

---

## 🎮 Controles

| Entrada | Ação |
|---|---|
| **Mouse** | Clique sobre os cartões (Fogo, Água, Terra, Ar) e botões de interface |
| **Teclas 1, 2, 3, 4** | Seleção rápida dos elementos Fogo, Água, Terra e Ar, respectivamente |
| **Enter** | Iniciar partida no Menu ou Reiniciar após Fim de Jogo |
| **P** ou **Esc** | Pausar ou Retomar a partida a qualquer momento |
| **M** | Silenciar ou Reativar os efeitos sonoros |

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.10 ou superior (testado em Python 3.13 e 3.14).
- Pygame-CE (`pip install pygame-ce`).

### Execução Normal

Na pasta raiz do projeto:

```bash
python3 main.py
```

### Execução Headless (Servidores / CI sem display)

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 main.py
```

---

## 🧪 Testes e Validação

O projeto conta com suíte completa de testes automatizados com `pytest` e scripts auxiliares para simulação e captura de telas:

### Suíte de Testes com Pytest

```bash
pytest testes/ -v
```

Cobre:
- Sequência inicial de 1 nota e acréscimo de exatamente 1 nota por rodada.
- Validação de respostas parciais e detecção precisa de erros (primeira e última posição).
- Bloqueio de cliques em estados não interativos (`DEMONSTRANDO`, `PAUSADO`, `FIM`).
- Preservação de timers e índices ao pausar e retomar.
- Limites numéricos PCM (int16: -32768 a 32767), número de amostras e teste de síntese de A4 (440 Hz).
- Tratamento gracioso para ambientes sem dispositivo de áudio.

### Script de Simulação Scripted (Smoke Test)

Simula automaticamente 4 rodadas bem-sucedidas e 1 erro proposital de forma headless:

```bash
python3 scripts/smoke_scripted.py
```

### Captura Automatizada de Screenshots

Gera capturas de tela do menu principal e da tela de demonstração salvando em `prints/`:

```bash
python3 scripts/capturar_screenshots.py
```

---

## 🎨 Assets e Recursos

- **Ícones Flat**: Localizados em `assets/imagens/` (`fogo.png`, `agua.png`, `terra.png`, `ar.png`). Fazem parte do pack didático de sprites flat originais projetados especificamente para a trilha didática do curso, com design minimalista sem gradientes, glow ou simulações tridimensionais.
- **Áudio Sintetizado**: O projeto **não utiliza arquivos externos WAV ou MP3**. Todas as notas musicais são geradas programmaticamente na inicialização do jogo através da biblioteca padrão (`math` e `array`), demonstrando na prática como a física ondulatória se traduz em som digital.
