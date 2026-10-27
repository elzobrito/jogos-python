# -*- coding: utf-8 -*-
"""Simulação de mundo em passo fixo, física vertical e colisão one-way (SPEC §0.2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from egg_game.core.camera import VerticalCamera
from egg_game.core.constants import (
    DEFAULT_SEED,
    FIXED_DT,
    GRAVITY,
    LOGICAL_H,
    MAX_FALL_SPEED,
    NEST_WORLD_Y,
    START_WORLD_Y,
)
from egg_game.core.generator import LevelGenerator
from egg_game.core.platforms import Platform
from egg_game.core.player import Player
from egg_game.core.score import ScoreTracker
from egg_game.core.states import EggState


@dataclass
class StepEvents:
    """Eventos semânticos ocorridos durante um passo de simulação (para áudio/UI)."""

    jumped: bool = False
    landed: bool = False
    cracked: bool = False
    victory: bool = False
    game_over: bool = False


@dataclass
class WorldSimulation:
    """
    Simulação completa do mundo do jogo em coordenadas lógicas (720x1280),
    totalmente desacoplada de Pygame/SDL (SPEC §4).
    """

    seed: int = DEFAULT_SEED
    target_nest_y: float = NEST_WORLD_Y
    player: Player = field(default_factory=Player)
    platforms: List[Platform] = field(default_factory=list)
    camera: VerticalCamera = field(default_factory=VerticalCamera)
    score: ScoreTracker = field(default_factory=ScoreTracker)
    generator: LevelGenerator = field(init=False)
    accumulator: float = 0.0
    elapsed_time: float = 0.0

    def __post_init__(self) -> None:
        self.reset(seed=self.seed, target_nest_y=self.target_nest_y)

    def reset(self, seed: Optional[int] = None, target_nest_y: Optional[float] = None) -> None:
        """Reinicia o mundo com a seed informada e posiciona o ovo na cesta de partida."""
        if seed is not None:
            self.seed = int(seed)
        if target_nest_y is not None:
            self.target_nest_y = float(target_nest_y)

        self.generator = LevelGenerator(seed=self.seed, target_nest_y=self.target_nest_y)
        self.platforms = []
        cesta_inicial = self.generator.create_start_platform(START_WORLD_Y)
        self.platforms.append(cesta_inicial)
        self.generator.generate_up_to(self.platforms, self.camera.y - LOGICAL_H)

        self.player = Player(
            x=cesta_inicial.x,
            y=cesta_inicial.y,
            prev_x=cesta_inicial.x,
            prev_y=cesta_inicial.y,
            state=EggState.IDLE,
            attached_platform_id=cesta_inicial.id,
        )
        self.camera.reset(START_WORLD_Y)
        self.score.reset(START_WORLD_Y)
        self.accumulator = 0.0
        self.elapsed_time = 0.0

    def get_platform_by_id(self, platform_id: Optional[str]) -> Optional[Platform]:
        if platform_id is None:
            return None
        for plat in self.platforms:
            if plat.id == platform_id:
                return plat
        return None

    def request_jump(self) -> bool:
        """Solicita o pulo do ovo (só atua se estiver pousado numa cesta)."""
        return self.player.jump()

    def update(self, dt: float) -> StepEvents:
        """
        Avança a simulação usando acumulador de timestep fixo (`FIXED_DT = 1/120 s`),
        garantindo independência de FPS.
        """
        eventos_agregados = StepEvents()
        dt_clamped = min(max(0.0, dt), 0.1)
        self.accumulator += dt_clamped

        while self.accumulator >= FIXED_DT:
            self.accumulator -= FIXED_DT
            ev = self.step_fixed(FIXED_DT)
            eventos_agregados.jumped = eventos_agregados.jumped or ev.jumped
            eventos_agregados.landed = eventos_agregados.landed or ev.landed
            eventos_agregados.cracked = eventos_agregados.cracked or ev.cracked
            eventos_agregados.victory = eventos_agregados.victory or ev.victory
            eventos_agregados.game_over = eventos_agregados.game_over or ev.game_over

        return eventos_agregados

    def step_fixed(self, dt: float = FIXED_DT) -> StepEvents:
        """Executa exatamente um passo de simulação física de duração `dt`."""
        eventos = StepEvents()
        self.elapsed_time += dt
        self.player.anim_time += dt

        # 1. Se o ovo estiver em animação de morte (DYING), avança o timer até DEAD
        if self.player.state == EggState.DYING:
            self.player.death_timer += dt
            if self.player.death_timer >= 0.75:
                self.player.state = EggState.DEAD
                eventos.game_over = True
            return eventos

        if self.player.state in (EggState.DEAD, EggState.CELEBRATING):
            return eventos

        # 2. Atualiza o movimento horizontal de todas as plataformas ativas
        deslocamentos: Dict[str, float] = {}
        for plat in self.platforms:
            deslocamentos[plat.id] = plat.step(dt)

        self.player.prev_x = self.player.x
        self.player.prev_y = self.player.y

        # 3. Caso o ovo esteja pousado numa cesta, ele viaja com ela (SPEC §0 / §0.2)
        if self.player.is_grounded and self.player.attached_platform_id is not None:
            cesta = self.get_platform_by_id(self.player.attached_platform_id)
            if cesta is not None:
                self.player.x = cesta.x
                self.player.y = cesta.y
                self.player.vx = cesta.vx
                self.player.vy = 0.0
                if self.player.state == EggState.LANDING:
                    self.player.landing_timer -= dt
                    if self.player.landing_timer <= 0.0:
                        self.player.state = EggState.IDLE
            else:
                self.player.attached_platform_id = None
                self.player.state = EggState.DESCENDING

        # 4. Caso o ovo esteja no ar, X permanece fixo no mundo e Y sofre gravidade
        if not self.player.is_grounded:
            self.player.vx = 0.0
            vy_anterior = self.player.vy
            self.player.vy = min(MAX_FALL_SPEED, self.player.vy + GRAVITY * dt)
            # Integração exata da posição vertical (trapezoidal)
            self.player.y += 0.5 * (vy_anterior + self.player.vy) * dt

            if self.player.vy < 0.0:
                self.player.state = EggState.ASCENDING
            else:
                self.player.state = EggState.DESCENDING
                # 5. Resolução de colisão one-way somente durante a descida (vy > 0)
                cesta_pouso = self._check_one_way_landing(self.player.prev_y, self.player.y, self.player.x)
                if cesta_pouso is not None:
                    self.player.land_on(
                        cesta_pouso.id,
                        cesta_pouso.x,
                        cesta_pouso.y,
                        is_nest=cesta_pouso.is_nest,
                    )
                    if cesta_pouso.is_nest:
                        eventos.victory = True
                    else:
                        eventos.landed = True

        # 6. Atualiza câmera, pontuação e geração contínua de cestas acima
        self.camera.update(self.player.y)
        self.score.update(self.player.y)
        self.generator.generate_up_to(self.platforms, self.camera.y - LOGICAL_H * 0.8)

        # Remove plataformas muito abaixo da câmera (preservando margem de queda recuperável)
        limite_descarte = self.camera.y + LOGICAL_H + 380.0
        self.platforms = [
            p for p in self.platforms
            if p.y <= limite_descarte or p.id == self.player.attached_platform_id
        ]

        # 7. Verifica queda além do limite inferior visível da câmera -> quebra do ovo
        if self.player.y > self.camera.bottom_limit_y:
            self.player.start_dying()
            eventos.cracked = True

        return eventos

    def _check_one_way_landing(
        self,
        prev_y: float,
        curr_y: float,
        egg_x: float,
    ) -> Optional[Platform]:
        """
        Detecta cruzamento descendente do topo de qualquer plataforma ativa
        (anti-tunneling: `prev_y <= plat.y <= curr_y`).
        """
        if curr_y < prev_y:
            return None

        candidatas: List[Platform] = []
        for plat in self.platforms:
            # Permite pequena tolerância vertical de 3px para contatos rasantes no topo
            if (prev_y - 3.0) <= plat.y <= (curr_y + 2.0):
                margem_util = plat.width * 0.44
                if abs(egg_x - plat.x) <= margem_util:
                    candidatas.append(plat)

        if not candidatas:
            return None

        # Se cruzou mais de uma no mesmo passo, escolhe a mais alta (menor Y)
        return min(candidatas, key=lambda p: p.y)
