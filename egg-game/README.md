# Egg Game: De Volta ao Ninho (MVP Aventura)

Jogo 2D vertical em retrato (`720×1280`, proporção `9:16`) desenvolvido em **Python 3 + Pygame-CE**, seguindo estritamente a especificação técnica em `SPEC.md` (incluindo o overhaul visual de UI/HUD v2 da §10 e a arquitetura de cenário em paralaxe + árvore modular v3 da §11).

---

## Decisão de Mecânica Central (`SPEC.md` §0)

> **Toque/Espaço para pular; as cestas se movem, calcule o momento.**  
> O ovo **NÃO tem controle lateral** — o jogador **só PULA** (`Espaço` / `Seta para cima ↑` / clique do mouse / toque em qualquer lugar da tela).

- O ovo permanece **horizontalmente centrado** na tela lógica (`X = 360`).
- O que se move horizontalmente é o **cenário**: as cestas suspensas nos galhos deslizam (`slide` com rebote nas bordas) ou oscilam (`oscillating` em movimento harmônico) com velocidades, amplitudes e fases variadas.
- **Pouso (`one-way`)**: ao cruzar o topo de uma cesta durante a descida (`vy > 0`), o ovo pousa sobre a palha e **viaja junto com a cesta** até que o jogador comande o próximo pulo (não há pulo automático ao pousar).
- **Salto**: ao pular, o ovo desacopla da cesta mantendo sua coordenada `X` de mundo do instante da decolagem e descreve uma trajetória vertical sob gravidade (`2400 px/s²`, impulso `-950 px/s`), enquanto as cestas continuam se movendo.
- **Objetivo (Modo Aventura)**: escalar a árvore modular de cesta em cesta até alcançar o **ninho final a 120 metros** (`100 px = 1 m`), sustentado por `tronco_topo.png`, para reencontrar a família. Caso erre o tempo do pulo e caia além da base visível da câmera sem aterrissar numa cesta inferior, ocorre a animação cartunesca de rachadura da casca com gema (`DEATH_ANIMATION` → `GAME_OVER`).

---

## Controles

| Contexto | Desktop | Toque / Mouse |
|---|---|---|
| **Pular** (único controle de movimento) | `Espaço`, `Seta para Cima (↑)` ou `W` | Clique ou toque em qualquer lugar da área de jogo |
| **Pausar / Retomar** | `Esc`, `P` ou botão de madeira `\|\|` na HUD | Toque no botão de pausa no canto superior direito |
| **Confirmar / Iniciar / Reiniciar** | `Enter`, `Espaço` ou `R` | Toque nos botões de madeira/verde nas telas |

---

## Como Rodar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Preparar os assets visuais (sprites, UI v2 e cenário modular v3)
```bash
# Sprites do ovo, cestas, ninho e itens a partir de ref/ref_1.jpg -> assets/sprites/
python3 tools/recortar_sprites.py

# Telas em retrato e placas de madeira de HUD (ALTURA / RECORDE / PAUSA) de ref/v2/ -> assets/bg/
python3 tools/extrair_assets_v2.py

# Cenário v3: camadas de paralaxe de ref/v3/paisagem_limpa.png -> assets/backgrounds/
# e árvore modular sem costura de ref/v3/tronco_bruto_1..7.png -> assets/tree/ + tools/teste_tronco.png
python3 tools/preparar_cenario.py
```

### 3. Executar os testes automatizados (headless, sem abrir janela)
```bash
pytest -q
```

### 4. Jogar normalmente
```bash
python3 main.py
```

### 5. Executar o modo demonstração (`--demo`)
```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 45 python3 main.py --demo
```
No modo `--demo`, o piloto automático navega pelas telas, calcula a janela temporal de alinhamento das cestas, executa saltos na árvore e salva automaticamente 6 capturas de tela em `prints/`:
- `prints/titulo.png` (Menu principal — *Egg Game: De Volta ao Ninho*)
- `prints/modo.png` (Seleção de Modo — Aventura 120 m / Infinito Em Breve)
- `prints/jogo.png` (Gameplay com vale pintado em paralaxe + tronco modular + HUD de madeira)
- `prints/pausa.png` (Modal de pausa em madeira sobre a partida)
- `prints/gameover.png` (Tela de Fim de Jogo com placa dinâmica de Altura e Recorde)
- `prints/vitoria.png` (Tela de Vitória ao alcançar o ninho em 120 m)

---

## Arquitetura do Projeto

O código separa rigorosamente o **núcleo de regras** (`egg_game/core/`, 100% puro Python e sem importação de `pygame`) da **camada de apresentação e plataforma** (`egg_game/render/`, `egg_game/audio/` e `egg_game/app.py`):

```text
egg-game/
  PRD.md
  SPEC.md
  README.md
  requirements.txt
  main.py                     # Ponto de entrada + flag --demo
  egg_game/
    __init__.py
    core/                     # Núcleo puro (sem Pygame/SDL)
      constants.py            # Dimensões 720x1280, gravidade, impulso, constantes
      states.py               # Enums AppState (incluindo MODE_SELECT) e EggState
      platforms.py            # Cestas (slide, oscillating, start) e ninho final
      player.py               # Modelo do ovo (acoplamento na cesta e pulo sob comando)
      generator.py            # LevelGenerator determinístico + ReachabilityValidator
      camera.py               # Câmera vertical unidirecional e centralização X
      score.py                # Cálculo de altura em metros (100px = 1m) e SaveRepository JSON
      physics.py              # WorldSimulation em passo fixo (1/120 s) e colisão one-way
    render/
      assets.py               # Cache de sprites (assets/sprites/), UI v2 (assets/bg/) e cenário v3
      draw.py                 # Paralaxe v3 (0.05..0.30), árvore modular (1.0x), HUD e telas v2
    audio/
      synth.py                # Efeitos sonoros e música sintetizados via buffer PCM 16-bit
    app.py                    # Loop Pygame, eventos, estados e diretor do modo --demo
  tools/
    recortar_sprites.py       # Extração de sprites do ovo/cestas/ninho de ref/ref_1.jpg
    extrair_assets_v2.py      # Extração de telas e placas de madeira HUD de ref/v2/
    preparar_cenario.py       # Extração das camadas de paralaxe e árvore modular de ref/v3/
    contact_sheet.png         # Folha de inspeção visual dos sprites recortados
    teste_tronco.png          # Validação visual de 5 segmentos empilhados do tronco modular
  assets/
    sprites/                  # Sprites PNG RGBA recortados (ovo, cestas, ninho, itens)
    bg/                       # Telas base e placas de madeira HUD (ALTURA, RECORDE, PAUSA)
    backgrounds/              # Camadas de paralaxe v3 (ceu.png, nuvens.png, montanhas.png, vilarejo.png)
    tree/                     # Tronco modular (tronco_base/a/b/c/topo.png) + galhos/ + folhas/
  tests/
    test_core.py              # Suíte pytest cobrindo física, pouso, alcançabilidade e recordes
  prints/                     # 6 capturas geradas pelo modo --demo
```

---

## Nota sobre Arte e Assets (`PRD.md` §14 / `SPEC.md` §2.2, §10 e §11)

Os assets gráficos utilizados em `assets/sprites/`, `assets/bg/`, `assets/backgrounds/` e `assets/tree/` são **artes placeholder extraídas e processadas automaticamente via Pillow** a partir das folhas conceituais em `ref/` (`ref/ref_1.jpg`, `ref/v2/` e `ref/v3/`, sendo que os arquivos `ref/v3/estudo_*` são apenas estudos de composição e não são usados como assets finais). Conforme documentado no `PRD.md` (§14 / §14.1) e na `SPEC.md`, esses recortes viabilizam o MVP funcional com estética pintada fiel às referências, permanecendo **pendentes de revisão e acabamento humano final** para distribuição comercial.
