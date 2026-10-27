# -*- coding: utf-8 -*-
"""Modelo do protagonista (ovo) sem controle lateral, conforme SPEC §0."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from egg_game.core.constants import CENTER_X, JUMP_IMPULSE, START_WORLD_Y
from egg_game.core.states import EggState


@dataclass
class Player:
    """
    Representa o ovo protagonista (SPEC §0 e §0.2):
    - Não possui controle horizontal pelo jogador: o jogador apenas PULA.
    - Quando pousado sobre uma cesta (`attached_platform_id` definido),
      viaja junto com a cesta (`x` acompanha `platform.x` e `y = platform.y`).
    - Ao pular (`jump()`), desacopla da cesta, mantém o `x` de mundo do instante
      do pulo estável durante todo o voo (`vx = 0`) e recebe `vy = JUMP_IMPULSE`.
    """

    x: float = CENTER_X
    y: float = START_WORLD_Y
    vx: float = 0.0
    vy: float = 0.0
    prev_x: float = CENTER_X
    prev_y: float = START_WORLD_Y
    radius: float = 22.0
    state: EggState = EggState.IDLE
    attached_platform_id: Optional[str] = None
    landing_timer: float = 0.0
    death_timer: float = 0.0
    anim_time: float = 0.0

    @property
    def is_grounded(self) -> bool:
        """Indica se o ovo está pousado e acoplado a uma cesta."""
        return (
            self.attached_platform_id is not None
            and self.state in (EggState.IDLE, EggState.LANDING, EggState.CELEBRATING)
        )

    def jump(self) -> bool:
        """
        Executa o salto somente sob comando explícito quando o ovo está pousado
        em uma cesta (sem pulo automático ao pousar e sem pulo duplo no ar).
        """
        if not self.is_grounded or self.state in (EggState.DYING, EggState.DEAD, EggState.CELEBRATING):
            return False

        self.attached_platform_id = None
        self.vx = 0.0
        self.vy = JUMP_IMPULSE
        self.landing_timer = 0.0
        self.state = EggState.ASCENDING
        return True

    def land_on(self, platform_id: str, platform_x: float, platform_y: float, is_nest: bool = False) -> None:
        """Acopla o ovo ao topo da cesta ou ninho em que acabou de pousar."""
        self.attached_platform_id = platform_id
        self.x = platform_x
        self.y = platform_y
        self.prev_x = platform_x
        self.prev_y = platform_y
        self.vy = 0.0
        if is_nest:
            self.state = EggState.CELEBRATING
        else:
            self.state = EggState.LANDING
            self.landing_timer = 0.14

    def start_dying(self) -> None:
        """Inicia a sequência de quebra cartunesca (casca rachando + gema)."""
        if self.state not in (EggState.DYING, EggState.DEAD):
            self.attached_platform_id = None
            self.vx = 0.0
            self.vy = 0.0
            self.state = EggState.DYING
            self.death_timer = 0.0
