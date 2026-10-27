# -*- coding: utf-8 -*-
"""
Renderizador completo do Egg Game: De Volta ao Ninho em resolução lógica 720x1280 (9:16).
Implementa:
- Arquitetura de fundo em paralaxe por camadas v3 (`SPEC.md` §11):
  `ceu.png` (0.05), `nuvens.png` (0.10), `montanhas.png` (0.20), `vilarejo.png` (0.30).
- Árvore modular contínua v3 (`SPEC.md` §11):
  `tronco_base -> A -> C -> B -> A -> C... -> tronco_topo` movendo a 1.0x com a câmera,
  com `galhos/*.png` e `folhas/*.png` nas emendas e sustentando o ninho final a 120 m.
- Placas de madeira da HUD (`ALTURA #### m`, `RECORDE #### m`, botão de pausa) e telas
  em retrato v2 (`SPEC.md` §10).
- Sprites reais do ovo, cestas e ninho em `assets/sprites/` (`SPEC.md` §2).
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

import pygame

from egg_game.core.constants import (
    CENTER_X,
    LOGICAL_H,
    LOGICAL_W,
    NEST_HEIGHT_M,
    NEST_WORLD_Y,
    START_WORLD_Y,
)
from egg_game.core.physics import WorldSimulation
from egg_game.core.platforms import Platform
from egg_game.core.player import Player
from egg_game.core.score import GameSaveData
from egg_game.core.states import AppState, EggState
from egg_game.render.assets import AssetManager

# Posição inicial de câmera (`VerticalCamera.reset`)
START_CAM_Y = START_WORLD_Y - LOGICAL_H * 0.72


class GameRenderer:
    """Renderiza o estado do jogo e da interface em uma superfície lógica 720x1280."""

    def __init__(self, assets: AssetManager) -> None:
        self.assets = assets
        self.canvas = pygame.Surface((LOGICAL_W, LOGICAL_H))

        pygame.font.init()
        self.font_title = pygame.font.SysFont("dejavusans", 42, bold=True)
        self.font_subtitle = pygame.font.SysFont("dejavusans", 28, bold=True)
        self.font_hud_value = pygame.font.SysFont("dejavusans", 28, bold=True)
        self.font_plaque_val = pygame.font.SysFont("dejavusans", 30, bold=True)
        self.font_btn = pygame.font.SysFont("dejavusans", 24, bold=True)
        self.font_body = pygame.font.SysFont("dejavusans", 19, bold=True)
        self.font_small = pygame.font.SysFont("dejavusans", 16, bold=True)

        # Áreas clicáveis (em coordenadas lógicas 720x1280) atualizadas a cada frame
        self.ui_buttons: Dict[str, pygame.Rect] = {}

        # Partículas leves de folhas/pólen no ar
        rng = random.Random(2026)
        self.folhas_flutuantes: List[Tuple[float, float, float, int]] = [
            (rng.uniform(40, LOGICAL_W - 40), rng.uniform(0, LOGICAL_H), rng.uniform(18, 36), rng.choice([0, 1, 2]))
            for _ in range(14)
        ]

        # Pré-calcula a estrutura vertical determinística da árvore modular (1.0x câmera)
        # Sequência obrigatória SPEC §11.2: base -> A -> C -> B -> A -> C ... -> topo (em 120 m)
        self._tree_segments: List[Tuple[str, float, int]] = []
        self._build_modular_tree_layout()

    def _build_modular_tree_layout(self) -> None:
        """
        Monta a lista de segmentos da árvore em coordenadas Y de mundo (`world_y` do topo de cada peça),
        começando na base do tronco (`world_y_bottom = 1380.0`) e subindo com sequência
        `base -> A -> C -> B -> A -> C...` até `NEST_WORLD_Y` (-10980.0), onde `tronco_topo` sustenta o ninho.
        """
        self._tree_segments.clear()
        overlap = 2
        h_base = self.assets.tronco_base.get_height() if self.assets.tronco_base else 319
        h_a = self.assets.tronco_a.get_height() if self.assets.tronco_a else 227
        h_b = self.assets.tronco_b.get_height() if self.assets.tronco_b else 227
        h_c = self.assets.tronco_c.get_height() if self.assets.tronco_c else 227
        h_topo = self.assets.tronco_topo.get_height() if self.assets.tronco_topo else 244

        # Base ancorada no pé da tela inicial
        curr_bottom_y = START_WORLD_Y + 360.0  # 1380.0
        base_top_y = curr_bottom_y - h_base
        self._tree_segments.append(("base", base_top_y, 0))
        curr_bottom_y = base_top_y + overlap

        ciclo = [("a", h_a), ("c", h_c), ("b", h_b)]
        idx = 1
        limite_topo = NEST_WORLD_Y + 120.0
        while curr_bottom_y > limite_topo:
            kind, seg_h = ciclo[(idx - 1) % len(ciclo)]
            seg_top_y = curr_bottom_y - seg_h
            self._tree_segments.append((kind, seg_top_y, idx))
            curr_bottom_y = seg_top_y + overlap
            idx += 1

        # Segmento de topo (`tronco_topo.png`) sustentando o ninho final em 120 m (`NEST_WORLD_Y`)
        topo_top_y = curr_bottom_y - h_topo
        self._tree_segments.append(("topo", topo_top_y, idx))
        curr_bottom_y = topo_top_y + overlap
        idx += 1

        # Segmentos extras acima do ninho para garantir cobertura total da tela no topo
        for _ in range(4):
            kind, seg_h = ciclo[(idx - 1) % len(ciclo)]
            seg_top_y = curr_bottom_y - seg_h
            self._tree_segments.append((kind, seg_top_y, idx))
            curr_bottom_y = seg_top_y + overlap
            idx += 1

    # --------------------------------------------------------------------------
    # UTILITÁRIOS DE TEXTO COM CONTORNO EM MADEIRA/PERGAMINHO
    # --------------------------------------------------------------------------
    def _draw_outlined_text(
        self,
        font: pygame.font.Font,
        text: str,
        center: Tuple[int, int],
        fill_color: Tuple[int, int, int] = (255, 246, 210),
        outline_color: Tuple[int, int, int] = (52, 28, 12),
        outline_px: int = 2,
    ) -> None:
        """Renderiza texto bold arredondado com contorno escuro nítido."""
        surf_main = font.render(text, True, fill_color)
        surf_out = font.render(text, True, outline_color)
        rect = surf_main.get_rect(center=center)
        for dx in range(-outline_px, outline_px + 1):
            for dy in range(-outline_px, outline_px + 1):
                if dx == 0 and dy == 0:
                    continue
                if dx * dx + dy * dy <= outline_px * outline_px + 1:
                    self.canvas.blit(surf_out, (rect.x + dx, rect.y + dy))
        self.canvas.blit(surf_main, rect)

    # --------------------------------------------------------------------------
    # CENÁRIO V3: PARALAXE POR CAMADAS + ÁRVORE MODULAR (SPEC §11)
    # --------------------------------------------------------------------------
    def _draw_parallax_landscape(self, cam_y: float) -> None:
        """
        Desenha as 4 camadas horizontais extraídas de `ref/v3/paisagem_limpa.png` (SPEC §11.1 e §11.4):
        1. `ceu.png`       -> paralaxe 0.05 (tileável verticalmente sem costura)
        2. `nuvens.png`    -> paralaxe 0.10 (repete suavemente na subida)
        3. `montanhas.png` -> paralaxe 0.20 (desce e sai de vista conforme o ovo sobe)
        4. `vilarejo.png`  -> paralaxe 0.30 (ancorado na base; desce e sai de vista na subida)
        """
        # Quanto a câmera já subiu em pixels desde o início (sempre >= 0)
        climb_px = max(0.0, START_CAM_Y - cam_y)

        # 1. Céu (fator 0.05, tile vertical contínuo)
        ceu = self.assets.bg_ceu
        if ceu is not None:
            ch = ceu.get_height()
            offset_ceu = int(round(climb_px * 0.05)) % ch
            y0 = offset_ceu - ch
            while y0 < LOGICAL_H:
                self.canvas.blit(ceu, (0, y0))
                y0 += ch

        # 2. Nuvens (fator 0.10, repetindo em ciclo vertical para preencher o céu na subida)
        nuvens = self.assets.bg_nuvens
        if nuvens is not None:
            period_n = 680
            offset_nuvens = int(round(climb_px * 0.10)) % period_n
            y_n = offset_nuvens - period_n
            while y_n < LOGICAL_H:
                self.canvas.blit(nuvens, (0, y_n))
                y_n += period_n

        # 3. Montanhas (fator 0.20: começa em y=520 acima do vilarejo e desce ao subir)
        montanhas = self.assets.bg_montanhas
        if montanhas is not None:
            y_mtn = int(round(520.0 + climb_px * 0.20))
            if y_mtn < LOGICAL_H:
                self.canvas.blit(montanhas, (0, y_mtn))

        # 4. Vilarejo (fator 0.30: começa ancorado na base y=540 e desce ao subir)
        vilarejo = self.assets.bg_vilarejo
        if vilarejo is not None:
            y_vil_start = LOGICAL_H - vilarejo.get_height()  # 540
            y_vil = int(round(y_vil_start + climb_px * 0.30))
            if y_vil < LOGICAL_H:
                self.canvas.blit(vilarejo, (0, y_vil))

    def _get_trunk_surface(self, kind: str) -> Optional[pygame.Surface]:
        if kind == "base":
            return self.assets.tronco_base
        if kind == "a":
            return self.assets.tronco_a
        if kind == "b":
            return self.assets.tronco_b
        if kind == "c":
            return self.assets.tronco_c
        if kind == "topo":
            return self.assets.tronco_topo
        return self.assets.tronco_a

    def _draw_modular_tree(self, sim: WorldSimulation) -> None:
        """
        Arquitetura de árvore sem costura (Round 3 / protótipo Elzo):
        1. Repete `trunk_repeat.png` (casca contínua vertical) apenas na faixa visível da câmera (1.0x).
        2. Sobrepõe os módulos decorativos `trunk_A..G.png` periodicamente (a cada 290 px) de forma
           determinística + tufos de folhas (`folhas_*.png`) para esconder junções.
        """
        desloc_x = int(round((CENTER_X - sim.player.x) * 0.12))
        x_tree = min(0, max(-24, -10 + desloc_x))
        cam_y = sim.camera.y

        # 1. Núcleo verticalmente contínuo `trunk_repeat.png` (1.0x câmera)
        trunk_core = self.assets.trunk_repeat
        if trunk_core is not None:
            size_y = trunk_core.get_height()
            first = math.floor((cam_y - size_y) / size_y)
            last = math.ceil((cam_y + LOGICAL_H + size_y) / size_y)
            for i in range(first, last):
                sy = round(i * size_y - cam_y)
                self.canvas.blit(trunk_core, (x_tree, sy))

        # 2. Módulos decorativos `trunk_A..G.png` sobrepostos periodicamente + folhas
        parts = self.assets.tree_parts
        folhas = self.assets.tree_folhas
        if parts:
            spacing = 290
            first_p = math.floor((cam_y - spacing) / spacing)
            last_p = math.ceil((cam_y + LOGICAL_H + spacing) / spacing)
            for i in range(first_p, last_p):
                part = parts[i % len(parts)]
                sy = round(i * spacing - cam_y)
                self.canvas.blit(part, (x_tree, sy))
                if folhas:
                    f_a = folhas[i % len(folhas)]
                    ox_a = 48 + ((i * 43) % 92)
                    self.canvas.blit(f_a, (x_tree + ox_a, sy + 24))

    # --------------------------------------------------------------------------
    # SPRITES REAIS: CESTAS, NINHO (A 120 M) E OVO PROTAGONISTA
    # --------------------------------------------------------------------------
    def _draw_platforms(self, sim: WorldSimulation) -> None:
        """Renderiza todas as cestas visíveis e o ninho final (em 120 m) usando os sprites reais."""
        for plat in sim.platforms:
            sy = int(round(sim.camera.world_to_screen_y(plat.y)))
            if sy < -160 or sy > LOGICAL_H + 160:
                continue

            sx = int(round(sim.camera.world_to_screen_x(plat.x, sim.player.x)))

            if plat.is_nest:
                quadro_brilho = int(sim.elapsed_time * 4.0) % len(self.assets.nest_glow)
                sprite_ninho = self.assets.nest_glow[quadro_brilho]
                rect = sprite_ninho.get_rect(midtop=(sx, sy - 42))
                self.canvas.blit(sprite_ninho, rect)
            else:
                sprite_cesta = self.assets.get_basket_surface(plat.visual_variant, plat.width)
                rect = sprite_cesta.get_rect(midtop=(sx, sy - 18))
                self.canvas.blit(sprite_cesta, rect)

    def _select_egg_sprite(self, player: Player) -> pygame.Surface:
        """Seleciona o quadro real do ovo de acordo com o seu `EggState`."""
        t = player.anim_time
        if player.state in (EggState.DYING, EggState.DEAD):
            idx = min(len(self.assets.egg_death) - 1, int(player.death_timer * 5.5))
            return self.assets.egg_death[idx]

        if player.state == EggState.ASCENDING:
            idx = int(t * 10.0) % len(self.assets.egg_jump)
            return self.assets.egg_jump[idx]

        if player.state == EggState.DESCENDING:
            idx = int(t * 9.0) % len(self.assets.egg_fall)
            return self.assets.egg_fall[idx]

        if player.state == EggState.LANDING:
            base = self.assets.egg_idle[3]
            w, h = base.get_size()
            return pygame.transform.smoothscale(base, (int(w * 1.08), int(h * 0.88)))

        if player.state == EggState.CELEBRATING:
            return self.assets.egg_jump[4]

        idx = int(t * 3.5) % len(self.assets.egg_idle)
        return self.assets.egg_idle[idx]

    def _draw_player(self, sim: WorldSimulation) -> None:
        """Desenha o ovo centrado horizontalmente na tela (SPEC §0)."""
        sx = int(round(CENTER_X))
        sy = int(round(sim.camera.world_to_screen_y(sim.player.y)))
        sy = min(LOGICAL_H - 90, sy)

        sprite_ovo = self._select_egg_sprite(sim.player)
        offset_y = 10 if sim.player.is_grounded else 4
        rect = sprite_ovo.get_rect(midbottom=(sx, sy + offset_y))
        self.canvas.blit(sprite_ovo, rect)

    def _draw_floating_leaves(self, elapsed: float, reduced_motion: bool) -> None:
        """Partículas leves de folhas/pólen na árvore (desativadas se reduced_motion)."""
        if reduced_motion:
            return
        for fx, fy, vel, tom in self.folhas_flutuantes:
            px = int((fx + math.sin(elapsed * 1.4 + fy) * 28.0) % LOGICAL_W)
            py = int((fy + elapsed * vel) % LOGICAL_H)
            cor = (146, 204, 92) if tom == 0 else ((255, 238, 152) if tom == 1 else (106, 168, 64))
            pygame.draw.ellipse(self.canvas, cor, pygame.Rect(px, py, 9, 5))

    # --------------------------------------------------------------------------
    # HUD EM PLACAS DE MADEIRA V2 (`ALTURA #### m`, `RECORDE #### m`, PAUSA)
    # --------------------------------------------------------------------------
    def _draw_hud(self, sim: WorldSimulation, record_m: int, register_pause_btn: bool = True) -> None:
        """
        Desenha as placas de madeira v2 de `ALTURA` (esquerda), `RECORDE` (direita)
        e o botão de madeira de `PAUSA` (extrema direita) conforme `SPEC.md` §10.2.
        """
        record_efetivo = max(record_m, sim.score.height_m)

        # Placa esquerda: ALTURA #### m
        if self.assets.hud_placa_altura is not None:
            pos_alt = (14, 10)
            self.canvas.blit(self.assets.hud_placa_altura, pos_alt)
            self._draw_outlined_text(
                self.font_hud_value,
                f"{sim.score.height_m:04d} m",
                center=(pos_alt[0] + 97, pos_alt[1] + 114),
                fill_color=(255, 246, 214),
                outline_color=(48, 25, 10),
                outline_px=2,
            )

        # Placa direita: RECORDE #### m
        if self.assets.hud_placa_recorde is not None:
            pos_rec = (444, 10)
            self.canvas.blit(self.assets.hud_placa_recorde, pos_rec)
            self._draw_outlined_text(
                self.font_hud_value,
                f"{record_efetivo:04d} m",
                center=(pos_rec[0] + 84, pos_rec[1] + 110),
                fill_color=(255, 232, 128),
                outline_color=(48, 25, 10),
                outline_px=2,
            )

        # Botão de pausa em madeira no canto superior direito
        if self.assets.hud_btn_pausa is not None:
            pos_pausa = (624, 10)
            self.canvas.blit(self.assets.hud_btn_pausa, pos_pausa)
            rect_pause = pygame.Rect(pos_pausa[0], pos_pausa[1] + 40, 82, 88)
            if register_pause_btn:
                self.ui_buttons["pause"] = rect_pause

    # --------------------------------------------------------------------------
    # TELAS DE ESTADO EM RETRATO V2 (`SPEC.md` §10)
    # --------------------------------------------------------------------------
    def _draw_main_menu(self, save_data: GameSaveData) -> None:
        """
        Tela Inicial (`MAIN_MENU` -> `prints/titulo.png`):
        Usa a arte v2 `tela_menu_base.png` com título `"EGG GAME: DE VOLTA AO NINHO"` (nunca `"EGG JUMP"`)
        e registra as áreas clicáveis dos botões de madeira.
        """
        bg = self.assets.screens_v2.get("menu")
        if bg is not None:
            self.canvas.blit(bg, (0, 0))

        # Áreas clicáveis dos botões da placa de madeira central
        self.ui_buttons["open_mode_select"] = pygame.Rect(160, 468, 400, 92)   # JOGAR
        self.ui_buttons["play_adventure"] = pygame.Rect(160, 568, 400, 78)     # MODO AVENTURA
        self.ui_buttons["open_mode_select_inf"] = pygame.Rect(160, 654, 400, 76)  # MODO INFINITO
        self.ui_buttons["open_settings"] = pygame.Rect(160, 738, 400, 76)      # OPÇÕES
        self.ui_buttons["quit_game"] = pygame.Rect(160, 822, 400, 78)          # SAIR

    def _draw_mode_select(self, save_data: GameSaveData) -> None:
        """
        Tela de Seleção de Modo (`MODE_SELECT` -> `prints/modo.png`):
        Usa a arte v2 `tela_modo_base.png` com os cartões de Modo Aventura (120 m)
        e Modo Infinito (Em Breve), além do botão Voltar.
        """
        bg = self.assets.screens_v2.get("modo")
        if bg is not None:
            self.canvas.blit(bg, (0, 0))

        # Botão JOGAR do Modo Aventura (ou clique no cartão esquerdo inteiro)
        self.ui_buttons["play_adventure"] = pygame.Rect(45, 225, 315, 625)
        # Botão VOLTAR (no canto inferior esquerdo de tela_modo_base.png: x=55..280, y=885..980)
        self.ui_buttons["to_menu"] = pygame.Rect(55, 885, 230, 96)

    def _draw_intro(self) -> None:
        """
        Tela Como Jogar (`INTRO`):
        Usa `tela_comojogar_base.png` (que preserva as ilustrações à esquerda e limpa as 4 faixas
        de texto em `x=340..658`) e apresenta a mecânica real da SPEC §0 / §10.2:
        `"Toque/Espaço para pular; as cestas se movem, calcule o momento"` (sem setas A/D).
        """
        bg = self.assets.screens_v2.get("comojogar")
        if bg is not None:
            self.canvas.blit(bg, (0, 0))

        # Faixas de texto à direita das ilustrações pintadas (x=342..652)
        blocos = [
            (
                250,
                "1. SÓ UM COMANDO: PULAR!",
                "Toque/Espaço para pular;",
                "as cestas se movem, calcule o momento",
            ),
            (
                455,
                "2. VIAJE COM A CESTA",
                "Ao pousar, o ovo acompanha a cesta.",
                "Espere alinhar com a de cima e pule!",
            ),
            (
                715,
                "3. ATENÇÃO ÀS CESTAS",
                "As cestas deslizam e oscilam em",
                "ritmos variados pelos galhos.",
            ),
            (
                925,
                "4. META: NINHO A 120 m",
                "Suba de cesta em cesta até o topo",
                "da árvore para voltar à família!",
            ),
        ]

        for y_top, titulo, l1, l2 in blocos:
            s_tit = self.font_body.render(titulo, True, (84, 42, 16))
            s_l1 = self.font_small.render(l1, True, (108, 60, 26))
            s_l2 = self.font_small.render(l2, True, (108, 60, 26))
            self.canvas.blit(s_tit, (344, y_top))
            self.canvas.blit(s_l1, (344, y_top + 32))
            self.canvas.blit(s_l2, (344, y_top + 56))

        # Botão ENTENDI (já pintado na arte base na base do pergaminho)
        self.ui_buttons["start_playing"] = pygame.Rect(180, 1080, 360, 110)

    def _draw_paused(self, sim: WorldSimulation, save_data: GameSaveData) -> None:
        """
        Modal de Pausa (`PAUSED` -> `prints/pausa.png`):
        Escurece suavemente o cenário v3 em andamento, mantém a HUD de madeira no topo
        e exibe a placa de madeira `tela_pausa_painel.png` centralizada.
        """
        overlay = pygame.Surface((LOGICAL_W, LOGICAL_H), pygame.SRCALPHA)
        overlay.fill((16, 22, 28, 135))
        self.canvas.blit(overlay, (0, 0))

        # Mantém a HUD de madeira visível no topo como na referência v2
        self._draw_hud(sim, save_data.adventure_record_m, register_pause_btn=False)

        painel = self.assets.screens_v2.get("pausa_painel")
        if painel is not None:
            px = (LOGICAL_W - painel.get_width()) // 2
            py = 210
            self.canvas.blit(painel, (px, py))

        # Registra as áreas clicáveis dos 4 botões do painel de pausa v2
        # (CONTINUAR, REINICIAR, OPÇÕES, VOLTAR AO MENU)
        self.ui_buttons["resume"] = pygame.Rect(180, 420, 360, 105)
        self.ui_buttons["restart"] = pygame.Rect(180, 560, 360, 105)
        self.ui_buttons["open_settings"] = pygame.Rect(180, 700, 360, 105)
        self.ui_buttons["to_menu"] = pygame.Rect(180, 840, 360, 105)

    def _draw_settings(self, save_data: GameSaveData) -> None:
        """
        Tela de Opções (`SETTINGS`):
        Usa `tela_opcoes_base.png` e exibe o estado atual de Música, SFX e Movimento Reduzido.
        """
        bg = self.assets.screens_v2.get("opcoes")
        if bg is not None:
            self.canvas.blit(bg, (0, 0))

        status_mus = "LIGADA" if save_data.music_enabled else "DESLIGADA"
        status_sfx = "LIGADOS" if save_data.sfx_enabled else "DESLIGADOS"
        status_mot = "ATIVADO" if save_data.reduced_motion else "DESATIVADO"

        badge_mus = pygame.Rect(415, 422, 150, 42)
        badge_sfx = pygame.Rect(415, 514, 150, 42)
        badge_mot = pygame.Rect(415, 630, 150, 42)
        for rect, ativo in (
            (badge_mus, save_data.music_enabled),
            (badge_sfx, save_data.sfx_enabled),
            (badge_mot, save_data.reduced_motion),
        ):
            cor_bg = (88, 164, 48) if ativo else (138, 78, 44)
            pygame.draw.rect(self.canvas, cor_bg, rect, border_radius=10)
            pygame.draw.rect(self.canvas, (54, 30, 14), rect, 3, border_radius=10)

        self._draw_outlined_text(self.font_small, status_mus, badge_mus.center)
        self._draw_outlined_text(self.font_small, status_sfx, badge_sfx.center)
        self._draw_outlined_text(self.font_small, status_mot, badge_mot.center)

        self.ui_buttons["toggle_music"] = pygame.Rect(150, 405, 425, 75)
        self.ui_buttons["toggle_sfx"] = pygame.Rect(150, 495, 425, 75)
        self.ui_buttons["toggle_motion"] = pygame.Rect(150, 610, 425, 75)
        self.ui_buttons["close_settings"] = pygame.Rect(175, 815, 370, 95)

    def _draw_game_over(self, sim: WorldSimulation, save_data: GameSaveData) -> None:
        """
        Tela de Fim de Jogo (`GAME_OVER` -> `prints/gameover.png`):
        Usa `tela_gameover_base.png` (que preserva os cabeçalhos `"ALTURA"` à esquerda e `"RECORDE"`
        à direita em y=670..726) e desenha os números dinâmicos nas caixas limpas em y=732..832.
        """
        bg = self.assets.screens_v2.get("gameover")
        if bg is not None:
            self.canvas.blit(bg, (0, 0))

        record_efetivo = max(save_data.adventure_record_m, sim.score.height_m)
        # Coluna esquerda (abaixo de ALTURA: x=125..348, y=732..832)
        self._draw_outlined_text(
            self.font_plaque_val,
            f"{sim.score.height_m:04d} m",
            center=(236, 780),
            fill_color=(255, 248, 220),
            outline_color=(56, 28, 12),
            outline_px=3,
        )
        # Coluna direita (abaixo de RECORDE: x=402..618, y=732..832)
        self._draw_outlined_text(
            self.font_plaque_val,
            f"{record_efetivo:04d} m",
            center=(505, 780),
            fill_color=(255, 224, 96),
            outline_color=(56, 28, 12),
            outline_px=3,
        )

        self.ui_buttons["restart"] = pygame.Rect(130, 868, 460, 112)
        self.ui_buttons["to_menu"] = pygame.Rect(98, 1025, 245, 110)
        self.ui_buttons["open_mode_select"] = pygame.Rect(360, 1025, 265, 110)

    def _draw_victory(self, sim: WorldSimulation, save_data: GameSaveData) -> None:
        """
        Tela de Vitória (`VICTORY` -> `prints/vitoria.png`):
        Usa `tela_vitoria_base.png` (que preserva `"O ovo está de volta ao ninho!"` e os cabeçalhos
        `"ALTURA"` e `"RECORDE"` em y=790..836) e desenha `0120 m` nas caixas limpas em y=838..938.
        """
        bg = self.assets.screens_v2.get("vitoria")
        if bg is not None:
            self.canvas.blit(bg, (0, 0))

        record_efetivo = max(save_data.adventure_record_m, NEST_HEIGHT_M)
        # Coluna esquerda (abaixo de ALTURA: x=155..362, y=838..938)
        self._draw_outlined_text(
            self.font_plaque_val,
            f"{NEST_HEIGHT_M:04d} m",
            center=(256, 886),
            fill_color=(255, 248, 220),
            outline_color=(56, 28, 12),
            outline_px=3,
        )
        # Coluna direita (abaixo de RECORDE: x=395..602, y=838..938)
        self._draw_outlined_text(
            self.font_plaque_val,
            f"{record_efetivo:04d} m",
            center=(498, 886),
            fill_color=(255, 224, 96),
            outline_color=(56, 28, 12),
            outline_px=3,
        )

        self.ui_buttons["restart"] = pygame.Rect(145, 940, 445, 100)
        self.ui_buttons["to_menu"] = pygame.Rect(185, 1082, 360, 98)

    # --------------------------------------------------------------------------
    # PONTO DE ENTRADA DE RENDERIZAÇÃO POR QUADRO
    # --------------------------------------------------------------------------
    def render_frame(
        self,
        window_surface: pygame.Surface,
        app_state: AppState,
        sim: WorldSimulation,
        save_data: GameSaveData,
    ) -> pygame.Surface:
        """
        Renderiza o quadro completo em `self.canvas` (720x1280) e o apresenta
        na janela mantendo a proporção 9:16.
        """
        self.ui_buttons.clear()

        if app_state == AppState.MAIN_MENU:
            self._draw_main_menu(save_data)
        elif app_state == AppState.MODE_SELECT:
            self._draw_mode_select(save_data)
        elif app_state == AppState.INTRO:
            self._draw_intro()
        elif app_state == AppState.SETTINGS:
            self._draw_settings(save_data)
        elif app_state == AppState.GAME_OVER:
            self._draw_game_over(sim, save_data)
        elif app_state == AppState.VICTORY:
            self._draw_victory(sim, save_data)
        else:
            # PLAYING, PAUSED, DEATH_ANIMATION: desenha cenário v3 (paralaxe + árvore modular)
            self._draw_parallax_landscape(sim.camera.y)
            self._draw_modular_tree(sim)
            self._draw_platforms(sim)
            self._draw_player(sim)
            self._draw_floating_leaves(sim.elapsed_time, save_data.reduced_motion)

            if app_state == AppState.PAUSED:
                self._draw_paused(sim, save_data)
            else:
                self._draw_hud(sim, save_data.adventure_record_m, register_pause_btn=True)

        # Escala mantendo aspecto 9:16 para a superfície da janela
        win_w, win_h = window_surface.get_size()
        if (win_w, win_h) == (LOGICAL_W, LOGICAL_H):
            window_surface.blit(self.canvas, (0, 0))
        else:
            escala = min(win_w / LOGICAL_W, win_h / LOGICAL_H)
            scaled_w = max(1, int(round(LOGICAL_W * escala)))
            scaled_h = max(1, int(round(LOGICAL_H * escala)))
            ox = (win_w - scaled_w) // 2
            oy = (win_h - scaled_h) // 2
            window_surface.fill((22, 20, 18))
            escalada = pygame.transform.smoothscale(self.canvas, (scaled_w, scaled_h))
            window_surface.blit(escalada, (ox, oy))

        return self.canvas
