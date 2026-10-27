# SPEC — Egg Game: De Volta ao Ninho (MVP)

Adaptação implementável do PRD.md. Em conflito, esta SPEC (em especial a §0) prevalece.

## 0. Decisão de mecânica (sobrepõe o PRD)

**O ovo NÃO tem controle lateral.** O jogador só PULA (Espaço / Seta para cima / clique / toque em qualquer lugar da tela).

- O ovo permanece **horizontalmente centrado** na tela (posição X lógica fixa no centro).
- O que se move é o **cenário**: cestas e galhos deslizam horizontalmente (slide constante esquerda/direita e/ou oscilação), com velocidades e sentidos variados.
- O desafio é **cronometrar o pulo** para aterrissar na próxima cesta acima no instante em que ela passa sob o ovo.
- Ao pousar numa cesta: o ovo **viaja com ela** (a cesta carrega o ovo) até o próximo pulo.
- Ao errar: o ovo cai. Se aterrissar numa cesta inferior ainda visível, continua; caso contrário, quebra (animação cartunesca de rachadura + gema → game over).
- **Não** há impulso automático ao pousar (contrário ao PRD §6 / §7.2). O próximo salto exige novo comando do jogador.
- **Não** há movimento horizontal controlado pelo jogador (contrário ao PRD §7.2 / §7.3).

### 0.1 Controles (substitui PRD §7.3 no gameplay)

| Contexto | Desktop | Toque |
|---|---|---|
| Pular | Espaço / ↑ / clique | Toque em qualquer lugar |
| Pausar | Esc / P / botão HUD | Botão de pausa |
| Confirmar / reiniciar | Enter / Espaço / botão | Botão destacado |

### 0.2 Física adaptada (substitui trechos de PRD §7.2)

- Eixo X do ovo: fixo no centro lógico (`LOGICAL_W/2`). Velocidade horizontal do ovo = 0 em relação à tela; quando pousado, herda o movimento da cesta (mundo move sob ele; na prática o ovo acompanha a cesta no mundo até o jump).
- Gravidade atua no eixo Y. Valores preliminares (ajustáveis): gravidade `2400 px/s²`, impulso de pulo `-950 px/s`, timestep fixo `1/120 s`.
- Cestas são plataformas *one-way*: pouso válido só no topo durante descida (`vy > 0`); laterais/baixo não ativam.
- Detecção considera posição anterior e atual (anti-tunneling).
- Enquanto `IDLE`/`LANDING` sobre cesta: ovo.x segue cesta.x (centro sobre o topo); ovo.y = topo da cesta.
- Ao pular: desacopla da cesta, aplica impulso vertical, estado `ASCENDING` → `DESCENDING`.

### 0.3 Cestas no MVP (adapta PRD §8)

MVP Aventura inclui:
- **Cesta deslizante (slide):** move horizontalmente em velocidade constante; rebote nas bordas do mundo jogável ou wrap conforme implementação (preferir rebote com margem).
- **Cesta oscilante:** seno/ping-pong entre limites, amplitude e fase configuráveis.
- **Cesta de partida:** inicial, pode ser quase estática ou slide lento para ensinar o timing.
- **Ninho final:** plataforma segura especial no topo (~120 m).

Tipos V1/Futuro do PRD (pequena, frágil, impulso, falsa, gelo…) podem existir como *sprites* recortados, mas **não** precisam de regras distintas no MVP além de usarem a cesta padrão (slide/oscilante) se o gerador os escolher visualmente. Preferir no MVP visual da cesta trançada padrão (`pequena_02` / `folhas_*` como variações cosméticas).

### 0.4 Alcançabilidade (adapta PRD §9)

Definição MVP sob a nova mecânica: **sempre existe uma janela temporal** em que um pulo a partir da cesta atual (ovo centrado nela) aterrissa na próxima cesta principal, considerando:
- trajetória parabólica do ovo (X fixo na tela ⇒ no mundo o ovo sobe/desce no X da cesta de origem no instante do pulo — modelar claramente: no pulo o ovo mantém X de mundo do momento do desacoplar, e as cestas continuam se movendo);
- movimento da cesta-alvo no tempo de voo;
- largura útil de pouso.

Gerador (seed + progressão):
1. Âncora = última cesta alcançável.
2. Amostrar ΔY em ~85–140 px, tipo (slide/oscilante), velocidade/amplitude.
3. Simular fases do movimento da cesta-alvo; aceitar só se houver janela de timing ≥ margem mínima (ex.: ≥ 120 ms ou fração do período).
4. Garantir que falhar o timing ainda permita queda recuperável numa cesta inferior ocasionalmente nas faixas iniciais; no alto, miss = game over é aceitável se a cesta inferior saiu da vista.
5. Determinismo: mesma seed + mesmas entradas + mesma versão ⇒ mesma sequência.

### 0.5 Ciclo de gameplay (substitui PRD §6)

1. Título → intro ignorável → jogando.
2. Ovo sobre cesta de partida (centralizado).
3. Jogador pulam no timing; cenário (cestas) desliza.
4. Pouso válido: ovo viaja com a cesta; câmera sobe.
5. Aventura: ninho a 120 m → vitória. Queda irreversível → death anim → game over.

---

## 1. Escopo MVP

- Modo **Aventura** apenas (ninho a 120 m; 100 px mundo = 1 m).
- Estados: `BOOT`, `MAIN_MENU` (título), `INTRO` (skippable), `PLAYING`, `PAUSED`, `DEATH_ANIMATION`, `GAME_OVER`, `VICTORY`, `SETTINGS` (música on/off, sfx on/off).
- HUD: altitude (m), recorde do modo, botão pausa.
- Resolução lógica **720×1280** (9:16), janela escalada mantendo aspecto.
- Paralaxe de árvore (céu, folhas, galhos, tronco).
- Recordes persistidos (JSON) para Aventura.
- Sem Infinito no MVP (pode deixar stub no menu desabilitado).
- Sem multiplayer, compras, ads, vidas.

## 2. Arte — sprites reais (obrigatório)

**NÃO desenhar o ovo/cestas/ninho/itens proceduralmente.** Usar sprites recortados de `ref/ref_1.jpg`.

### 2.1 Script `tools/recortar_sprites.py` (Pillow)

- Entrada: `ref/ref_1.jpg` (1440×850, fundo bege ~`#E9E1D4` / RGB(233,225,212)).
- Grade: **8 colunas × 5 linhas**, célula ~180×170 px.
- Ordem das células (linha-major), labels na folha:
  - R0: idle_04, idle_01, idle_05, idle_03, idle_02, jump_06, jump_05, jump_03
  - R1: jump_01, jump_04, jump_02, fall_03, fall_01, fall_04, fall_02, death_03
  - R2: death_01, death_04, death_02, pequena_02, fragil_02, folhas_01, nuvem_02, folhas_02
  - R3: gelo_02, falsa_02, gelo_01, ninho_final, ninho_brilho_01, ninho_brilho_03, ninho_brilho_02, escudo
  - R4: pena, estrela, coracao, relogio, (células vazias restantes)
- Para cada célula: (1) crop da célula; (2) excluir faixa inferior do rótulo (~18–28 px ou detectar texto); (3) color-key / flood-fill do bege → alpha 0; (4) limpeza de halo nas bordas; (5) trim do bbox opaco; (6) salvar PNG RGBA.
- Saídas em `assets/sprites/` com nomes PRD:
  - `egg_idle_00.png` … (mapear idle_01..05 → índices estáveis)
  - `egg_jump_00.png` …
  - `egg_fall_00.png` …
  - `egg_death_00.png` …
  - `basket_static_01.png` ← pequena_02; `basket_leaves_01.png` ← folhas_01; `basket_leaves_02.png` ← folhas_02; `basket_fragile_01.png` ← fragil_02; `basket_cloud_01.png` ← nuvem_02; `basket_ice_01/02.png`; `basket_fake_01.png`
  - `nest_final.png`, `nest_glow_00.png` … (brilho_01..03)
  - `item_shield.png`, `item_feather.png`, `item_star.png`, `item_heart.png`, `item_clock.png`
- Também gerar `tools/contact_sheet.png` com todos os sprites recortados para inspeção.
- `ref_2`..`ref_7`: se tiverem camadas de fundo/UI limpas, recortar para `assets/bg/` ou `assets/ui/`; senão, desenhar céu/tronco/galhos/folhas em código **combinando** a paleta e o look das refs (fundo procedural OK; personagem/cestas/ninho **não**).

### 2.2 Runtime

- Carregar PNGs de `assets/sprites/`.
- README deve notar: arte placeholder recortada de concept sheets, pendente revisão humana (PRD §14).

## 3. Áudio

Efeitos sintetizados em código (`pygame.mixer.Sound` com buffer). Falhar gracefully sem áudio. Música/SFX togglable em Settings.

## 4. Arquitetura

Separar **núcleo** (física, colisão one-way, gerador+alcançabilidade, score, FSM do ovo/app) de **pygame** (render, input, audio, window).

Sugestão de layout:
```
egg-game/
  PRD.md SPEC.md README.md requirements.txt
  main.py                 # entry + --demo
  egg_game/
    __init__.py
    core/                 # sem pygame
      physics.py constants.py player.py platforms.py
      generator.py camera.py score.py states.py
    render/ assets.py draw.py
    audio/ synth.py
    app.py                # loop pygame
  tools/recortar_sprites.py
  assets/sprites/ ...
  tests/                  # pytest, headless
  prints/                 # saida do --demo
  ref/                    # concept art (já existe)
```

Comentários e README em **português**.

## 5. Testes (pytest)

Sem display. Cobrir no mínimo:
- física/pouso one-way e “ovo carrega com a cesta”;
- pulo só sob comando; X do ovo estável quando no ar (após desacoplar);
- gerador: alcançabilidade com seeds fixas;
- determinismo (mesma seed → mesmas plataformas);
- height_m / recorde.

## 6. Modo `--demo`

Piloto automático que estima a janela de timing e pula. Percorre título → (intro skip) → jogo → (forçar death ou vitória curta) e salva:
`prints/titulo.png`, `prints/jogo.png`, `prints/gameover.png`, `prints/vitoria.png`.
Headless: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`. Sair 0 em < 30 s.

## 7. Entregáveis

`main.py`, pacote `egg_game/`, `tools/recortar_sprites.py`, `assets/sprites/*`, `tools/contact_sheet.png`, `tests/`, `README.md` (como rodar, controles = só pular, arquitetura, §0 decisão de mecânica, nota de arte placeholder), `requirements.txt` (`pygame-ce`, `pytest`, `Pillow`).

## 8. Aceitação

1. `python3 tools/recortar_sprites.py` gera sprites + contact sheet.
2. `pytest -q` passa.
3. `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 30 python3 main.py --demo` exit 0 e escreve os 4 prints.
4. `prints/jogo.png` deve mostrar ovo cartoon + cestas numa árvore (sprites reais), não retângulos placeholder.

## 9. O que manter do PRD (não listado acima)

Paleta, tom, one-way platforms, câmera vertical (§10.1), altura em m e records (§10.2), paralaxe árvore (§10.3), progressão 0–120 m (§11) adaptada a cestas móveis desde cedo (ensinar timing), estados do app (§12), UX essencial (§13), inventário de áudio (§15), princípio de arquitetura (§16), empacotamento futuro fora do MVP.

---

## 10. Adendo visual v2 (sobrepõe arte procedural do render atual)

Refs oficiais em `ref/v2/`:
- `gameplay_mockup.png` — tronco à esquerda, vale/vilarejo pintado, cestas variadas, HUD madeira "ALTURA #### m" / "RECORDE #### m", botão pausa madeira.
- `tela_titulo.png`, `tela_modo.png`, `tela_pausa.png`, `tela_gameover.png`, `tela_comojogar.png` (paisagem).
- `telas_retrato.png` — **layout-alvo** 8 telas 9:16 (menu, modo, como jogar, gameplay, pausa, game over, vitória, opções).

### Obrigatório
1. Usar essas imagens como arte: fundos de tela a partir delas (crop/scale para 720×1280, blur/escurecer atrás de painéis); crop do vale + tronco de `gameplay_mockup` como camadas de paralaxe; crop cestas/ninhos/placas HUD/botões onde limpos.
2. Texto dinâmico (números, labels) com fonte bold arredondada sobre placas de madeira (crop ou desenho combinando o mockup). Labels HUD: **ALTURA** e **RECORDE** (não "ALTITUDE").
3. Substituir texto baked que contradiz a mecânica: Como Jogar = **"Toque/Espaço para pular; as cestas se movem, calcule o momento"** — NÃO A/D nem setas laterais.
4. Nome oficial: **"Egg Game: De Volta ao Ninho"** (nunca "Egg Jump" no produto).
5. `--demo` regenera prints: `titulo.png`, `modo.png`, `jogo.png`, `pausa.png`, `gameover.png`, `vitoria.png`.
6. Manter pytest passando e mecânica §0 intacta. Sprites do ovo de `assets/sprites/` continuam.

---

## 11. Adendo cenário v3 (sobrepõe fundos do §10 / crops de tronco de v2)

Refs em `ref/v3/`:
- `paisagem_limpa.png` (3840×2160) — paisagem limpa: céu, nuvens, montanhas, rio, vilarejo; **sem** árvore/texto.
- `tronco_bruto_1..7.png` — segmentos de tronco em fundo **branco** (precisam alpha real).
- `estudo_modular_1/2.png`, `estudo_composicao.png` — estudos de composição, **não** assets finais.

### Script `tools/preparar_cenario.py` (Pillow)

**1) Paralaxe a partir de `paisagem_limpa`:**
- Saídas: `assets/backgrounds/ceu.png`, `nuvens.png`, `montanhas.png`, `vilarejo.png`
- Dividir em faixas horizontais com máscaras alpha / bordas suaves (feather).
- Céu tileável verticalmente (altura infinita).
- Fatores de câmera: ceu ~0.05, nuvens 0.1, montanhas 0.2, vilarejo 0.3.
- Conforme o ovo sobe, vilarejo/montanhas descem e saem; restam céu + nuvens (nuvens repetem).

**2) Árvore modular a partir de `tronco_bruto_*`:**
- Remover fundo branco (flood-fill das bordas + defringe). Buracos internos tipo knothole: manter ou preencher com casca escura.
- Normalizar mesma largura de tronco; tornar topo/fundo seamless (crop em faixa reta comum, blend/cross-fade para casca/cores baterem).
- Saídas: `assets/tree/tronco_base.png`, `tronco_a.png`, `tronco_b.png`, `tronco_c.png`, `tronco_topo.png`, mais `assets/tree/galhos/` e `folhas/` (stubs/folhas recortados dos segmentos/estudos).
- Montagem in-game: base → A → C → B → A → C … com galhos/folhas para esconder repetição; árvore move a **1.0×** com a câmera; peça do topo segura o ninho a 120 m na Aventura.
- Verificar: `tools/teste_tronco.png` (5 segmentos empilhados) e `prints/jogo.png` — costuras não devem ser óbvias.

Manter do §10: UI/HUD madeira (ALTURA/RECORDE), telas a partir de v2/telas_retrato, como-jogar com mecânica de pulo, nome "Egg Game: De Volta ao Ninho", 6 prints no --demo, pytest.
