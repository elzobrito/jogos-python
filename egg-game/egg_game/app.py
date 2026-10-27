# -*- coding: utf-8 -*-
"""
Aplicação Pygame principal do Egg Game: De Volta ao Ninho.
Conecta o núcleo de simulação (`egg_game.core`), o renderizador (`egg_game.render`),
o sintetizador de áudio (`egg_game.audio`) e o piloto automático do modo `--demo`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import pygame

from egg_game.audio.synth import AudioService
from egg_game.core.constants import (
    DEFAULT_SEED,
    LOGICAL_H,
    LOGICAL_W,
    NEST_HEIGHT_M,
    NEST_WORLD_Y,
    START_WORLD_Y,
)
from egg_game.core.generator import ReachabilityValidator
from egg_game.core.physics import WorldSimulation
from egg_game.core.platforms import Platform
from egg_game.core.score import GameSaveData, SaveRepository
from egg_game.core.states import AppState, EggState
from egg_game.render.assets import AssetManager
from egg_game.render.draw import GameRenderer

DIRETORIO_RAIZ = Path(__file__).resolve().parent.parent
PASTA_PRINTS = DIRETORIO_RAIZ / "prints"


class EggGameApp:
    """Controlador de estados, eventos, áudio, renderização e modo `--demo`."""

    def __init__(self, demo_mode: bool = False, seed: int = DEFAULT_SEED) -> None:
        pygame.init()
        pygame.display.set_caption("Egg Game: De Volta ao Ninho")
        self.window = pygame.display.set_mode((LOGICAL_W, LOGICAL_H))
        self.clock = pygame.time.Clock()
        self.demo_mode = bool(demo_mode)
        self.seed = int(seed)
        self.should_quit = False

        # Persistência, áudio e assets reais
        self.save_repo = SaveRepository()
        self.save_data: GameSaveData = self.save_repo.load()
        self.audio = AudioService(
            music_enabled=self.save_data.music_enabled,
            sfx_enabled=self.save_data.sfx_enabled,
        )
        self.assets = AssetManager()
        self.assets.load_all()
        self.renderer = GameRenderer(self.assets)

        # Simulação do mundo
        self.sim = WorldSimulation(seed=self.seed, target_nest_y=NEST_WORLD_Y)
        self.state: AppState = AppState.BOOT
        self.previous_state_before_settings: AppState = AppState.MAIN_MENU
        self.return_state_after_intro: Optional[AppState] = None

        # Estado do roteiro automatizado `--demo` (6 prints exigidos na SPEC §10.3)
        self.demo_timer: float = 0.0
        self.demo_phase: str = "titulo"
        self.saved_titulo = False
        self.saved_modo = False
        self.saved_jogo = False
        self.saved_pausa = False
        self.saved_gameover = False
        self.saved_vitoria = False
        if self.demo_mode:
            PASTA_PRINTS.mkdir(parents=True, exist_ok=True)

        # Transição imediata BOOT -> MAIN_MENU
        self.state = AppState.MAIN_MENU
        self.audio.update_music_state(True)

    # --------------------------------------------------------------------------
    # TRANSIÇÕES DE ESTADO E AÇÕES DE JOGO
    # --------------------------------------------------------------------------
    def start_new_run(self, skip_intro: bool = False) -> None:
        """Inicia uma nova tentativa no modo Aventura."""
        if not skip_intro and not self.save_data.tutorial_seen and not self.demo_mode:
            self.return_state_after_intro = None
            self.state = AppState.INTRO
            return

        self.save_data.tutorial_seen = True
        self.save_repo.save(self.save_data)
        self.sim.reset(seed=self.seed, target_nest_y=NEST_WORLD_Y)
        self.state = AppState.PLAYING
        self.audio.update_music_state(True)

    def _window_to_logical(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Converte coordenada de clique da janela para a grade lógica 720x1280."""
        win_w, win_h = self.window.get_size()
        if (win_w, win_h) == (LOGICAL_W, LOGICAL_H):
            return pos
        escala = min(win_w / LOGICAL_W, win_h / LOGICAL_H)
        scaled_w = max(1, int(round(LOGICAL_W * escala)))
        scaled_h = max(1, int(round(LOGICAL_H * escala)))
        ox = (win_w - scaled_w) // 2
        oy = (win_h - scaled_h) // 2
        lx = int((pos[0] - ox) / max(1e-5, escala))
        ly = int((pos[1] - oy) / max(1e-5, escala))
        return (lx, ly)

    def _handle_button_click(self, btn_key: str) -> None:
        """Executa a ação associada a um botão da interface."""
        self.audio.play_sfx("ui_select")

        if btn_key in ("open_mode_select", "open_mode_select_inf"):
            self.state = AppState.MODE_SELECT
        elif btn_key == "play_adventure":
            self.start_new_run(skip_intro=False)
        elif btn_key == "start_playing":
            if self.return_state_after_intro is not None:
                self.state = self.return_state_after_intro
                self.return_state_after_intro = None
            else:
                self.start_new_run(skip_intro=True)
        elif btn_key == "how_to_play":
            self.return_state_after_intro = self.state
            self.state = AppState.INTRO
        elif btn_key == "pause":
            if self.state == AppState.PLAYING:
                self.state = AppState.PAUSED
                self.audio.update_music_state(False)
        elif btn_key == "resume":
            if self.state == AppState.PAUSED:
                self.sim.accumulator = 0.0
                self.state = AppState.PLAYING
                self.audio.update_music_state(True)
        elif btn_key == "restart":
            self.start_new_run(skip_intro=True)
        elif btn_key == "to_menu":
            self.state = AppState.MAIN_MENU
            self.audio.update_music_state(True)
        elif btn_key == "open_settings":
            self.previous_state_before_settings = self.state
            self.state = AppState.SETTINGS
        elif btn_key == "close_settings":
            self.state = self.previous_state_before_settings
        elif btn_key == "toggle_music":
            self.save_data.music_enabled = not self.save_data.music_enabled
            self.audio.set_music_enabled(self.save_data.music_enabled)
            self.save_repo.save(self.save_data)
        elif btn_key == "toggle_sfx":
            self.save_data.sfx_enabled = not self.save_data.sfx_enabled
            self.audio.set_sfx_enabled(self.save_data.sfx_enabled)
            self.save_repo.save(self.save_data)
        elif btn_key == "toggle_motion":
            self.save_data.reduced_motion = not self.save_data.reduced_motion
            self.save_repo.save(self.save_data)
        elif btn_key == "quit_game":
            self.should_quit = True

    def _trigger_player_jump(self) -> None:
        """Dispara o pulo do ovo quando em `PLAYING`."""
        if self.state == AppState.PLAYING:
            if self.sim.request_jump():
                self.audio.play_sfx("jump")

    # --------------------------------------------------------------------------
    # PROCESSAMENTO DE EVENTOS (DESKTOP E TOQUE)
    # --------------------------------------------------------------------------
    def process_events(self) -> bool:
        """Lê eventos do Pygame. Retorna False caso a janela deva fechar."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.WINDOWFOCUSLOST and not self.demo_mode:
                if self.state == AppState.PLAYING:
                    self.state = AppState.PAUSED
                    self.audio.update_music_state(False)

            if event.type == pygame.KEYDOWN:
                if self.state == AppState.MAIN_MENU:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_UP):
                        self._handle_button_click("open_mode_select")
                    elif event.key == pygame.K_ESCAPE:
                        return False

                elif self.state == AppState.MODE_SELECT:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_UP):
                        self._handle_button_click("play_adventure")
                    elif event.key == pygame.K_ESCAPE:
                        self._handle_button_click("to_menu")

                elif self.state == AppState.INTRO:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_UP, pygame.K_ESCAPE):
                        self._handle_button_click("start_playing")

                elif self.state == AppState.PLAYING:
                    # §0.1: Jogador só PULA (Espaço / Seta para cima) ou pausa (Esc / P)
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        self._trigger_player_jump()
                    elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self._handle_button_click("pause")

                elif self.state == AppState.PAUSED:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_SPACE, pygame.K_RETURN):
                        self._handle_button_click("resume")
                    elif event.key == pygame.K_r:
                        self._handle_button_click("restart")

                elif self.state == AppState.SETTINGS:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        self._handle_button_click("close_settings")

                elif self.state in (AppState.GAME_OVER, AppState.VICTORY):
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r, pygame.K_UP):
                        self._handle_button_click("restart")
                    elif event.key == pygame.K_ESCAPE:
                        self._handle_button_click("to_menu")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                lpos = self._window_to_logical(event.pos)
                clicou_botao = False
                for key, rect in list(self.renderer.ui_buttons.items()):
                    if rect.collidepoint(lpos):
                        self._handle_button_click(key)
                        clicou_botao = True
                        break

                if self.should_quit:
                    return False

                # Em PLAYING, clicar ou tocar em qualquer lugar fora do botão de pausa faz o ovo PULAR
                if not clicou_botao:
                    if self.state == AppState.PLAYING:
                        self._trigger_player_jump()
                    elif self.state == AppState.INTRO:
                        self._handle_button_click("start_playing")

        return not self.should_quit

    # --------------------------------------------------------------------------
    # PILOTO AUTOMÁTICO E CAPTURA DOS 6 PRINTS DO MODO `--demo` (SPEC §6 e §10.3)
    # --------------------------------------------------------------------------
    def _find_next_platform_above(self) -> Optional[Platform]:
        """Retorna a cesta imediatamente acima do ovo para o piloto automático."""
        acima = [
            p for p in self.sim.platforms
            if p.y < self.sim.player.y - 25.0 and (self.sim.player.y - p.y) <= 182.0
        ]
        if not acima:
            return None
        return max(acima, key=lambda p: p.y)

    def _run_autopilot_step(self) -> None:
        """
        Piloto automático do `--demo`: quando o ovo está pousado numa cesta,
        estima a posição futura da próxima cesta no instante de pouso e pula
        quando a janela de timing está alinhada.
        """
        if not self.sim.player.is_grounded:
            return

        cesta_atual = self.sim.get_platform_by_id(self.sim.player.attached_platform_id)
        proxima = self._find_next_platform_above()
        if cesta_atual is None or proxima is None:
            return

        if ReachabilityValidator.can_land_if_jump_after(
            cesta_atual,
            proxima,
            delay_s=0.0,
            margin_ratio=0.26,
        ):
            self._trigger_player_jump()

    def _update_demo_director(self, dt: float, canvas: pygame.Surface) -> bool:
        """
        Conduz a demonstração automática e salva os 6 prints exigidos na SPEC §10.3:
        1. `prints/titulo.png`
        2. `prints/modo.png`
        3. `prints/jogo.png`
        4. `prints/pausa.png`
        5. `prints/gameover.png`
        6. `prints/vitoria.png`
        Retorna False quando todos os 6 prints foram salvos para encerrar com exit 0.
        """
        self.demo_timer += dt

        if self.demo_phase == "titulo":
            if not self.saved_titulo and self.demo_timer >= 0.12:
                pygame.image.save(canvas, str(PASTA_PRINTS / "titulo.png"))
                self.saved_titulo = True
            if self.demo_timer >= 0.24:
                self.state = AppState.MODE_SELECT
                self.demo_phase = "modo"
                self.demo_timer = 0.0

        elif self.demo_phase == "modo":
            if not self.saved_modo and self.demo_timer >= 0.12:
                pygame.image.save(canvas, str(PASTA_PRINTS / "modo.png"))
                self.saved_modo = True
            if self.demo_timer >= 0.24:
                self.start_new_run(skip_intro=True)
                self.demo_phase = "jogando"
                self.demo_timer = 0.0

        elif self.demo_phase == "jogando":
            self._run_autopilot_step()
            # Captura `prints/jogo.png` quando o ovo já subiu algumas cestas e está em ação
            if not self.saved_jogo and self.demo_timer >= 1.35:
                pygame.image.save(canvas, str(PASTA_PRINTS / "jogo.png"))
                self.saved_jogo = True
                # Abre o modal de pausa para capturar `prints/pausa.png`
                self.state = AppState.PAUSED
                self.demo_phase = "pausa"
                self.demo_timer = 0.0

        elif self.demo_phase == "pausa":
            if not self.saved_pausa and self.demo_timer >= 0.15:
                pygame.image.save(canvas, str(PASTA_PRINTS / "pausa.png"))
                self.saved_pausa = True
            if self.demo_timer >= 0.30:
                self.state = AppState.PLAYING
                self.demo_phase = "forcar_queda"
                self.demo_timer = 0.0

        elif self.demo_phase == "forcar_queda":
            # Força uma queda irreversível para acionar DEATH_ANIMATION -> GAME_OVER
            if self.state == AppState.PLAYING and self.demo_timer >= 0.12:
                self.sim.player.start_dying()
                self.state = AppState.DEATH_ANIMATION
                self.audio.play_sfx("crack")

            if self.state == AppState.GAME_OVER and not self.saved_gameover and self.demo_timer >= 0.95:
                pygame.image.save(canvas, str(PASTA_PRINTS / "gameover.png"))
                self.saved_gameover = True
                # Inicia a demonstração da chegada ao ninho final (120 m) para `prints/vitoria.png`
                self.sim.reset(seed=self.seed, target_nest_y=NEST_WORLD_Y)
                y_aprox = START_WORLD_Y - 119.0 * 100.0
                cesta_aprox = Platform(
                    id="demo-aprox",
                    kind="slide",
                    x=360.0,
                    y=y_aprox,
                    width=150.0,
                    speed=28.0,
                    visual_variant="basket_leaves_01",
                )
                ninho_final = Platform(
                    id="demo-nest",
                    kind="nest",
                    x=360.0,
                    y=NEST_WORLD_Y,
                    width=210.0,
                    speed=0.0,
                    visual_variant="nest_final",
                )
                self.sim.platforms = [cesta_aprox, ninho_final]
                self.sim.player.land_on(cesta_aprox.id, cesta_aprox.x, cesta_aprox.y, is_nest=False)
                self.sim.player.state = EggState.IDLE
                self.sim.camera.update(self.sim.player.y)
                self.sim.score.update(self.sim.player.y)
                self.state = AppState.PLAYING
                self.demo_phase = "rumo_vitoria"
                self.demo_timer = 0.0

        elif self.demo_phase == "rumo_vitoria":
            if self.state == AppState.PLAYING:
                self._run_autopilot_step()
            elif self.state == AppState.VICTORY:
                if not self.saved_vitoria and self.demo_timer >= 0.80:
                    pygame.image.save(canvas, str(PASTA_PRINTS / "vitoria.png"))
                    self.saved_vitoria = True
                if self.saved_vitoria and self.demo_timer >= 0.95:
                    return False

        return True

    # --------------------------------------------------------------------------
    # LOOP PRINCIPAL DA APLICAÇÃO
    # --------------------------------------------------------------------------
    def update_simulation(self, dt: float) -> None:
        """Atualiza a simulação física quando em `PLAYING` ou `DEATH_ANIMATION`."""
        if self.state in (AppState.MAIN_MENU, AppState.MODE_SELECT, AppState.INTRO, AppState.SETTINGS):
            self.sim.elapsed_time += dt
            return

        if self.state == AppState.PAUSED:
            return

        if self.state in (AppState.PLAYING, AppState.DEATH_ANIMATION):
            eventos = self.sim.update(dt)

            if eventos.landed:
                self.audio.play_sfx("land")

            if eventos.cracked:
                self.state = AppState.DEATH_ANIMATION
                self.audio.play_sfx("crack")

            if self.sim.score.height_m > self.save_data.adventure_record_m:
                self.save_data.adventure_record_m = self.sim.score.height_m
                self.save_repo.save(self.save_data)

            if eventos.victory:
                self.sim.score.update(NEST_WORLD_Y)
                if self.sim.score.height_m > self.save_data.adventure_record_m:
                    self.save_data.adventure_record_m = self.sim.score.height_m
                    self.save_repo.save(self.save_data)
                self.state = AppState.VICTORY
                self.audio.play_sfx("victory")

            if eventos.game_over:
                self.state = AppState.GAME_OVER
                self.audio.play_sfx("game_over")

    def run(self) -> int:
        """Executa o loop principal a 60 FPS."""
        running = True
        while running:
            dt_raw = self.clock.tick(60) / 1000.0
            dt = min(dt_raw if dt_raw > 0.0 else (1.0 / 60.0), 0.05)

            running = self.process_events()
            if not running:
                break

            self.update_simulation(dt)
            canvas = self.renderer.render_frame(self.window, self.state, self.sim, self.save_data)
            pygame.display.flip()

            if self.demo_mode:
                if not self._update_demo_director(dt, canvas):
                    break

        pygame.quit()
        return 0
