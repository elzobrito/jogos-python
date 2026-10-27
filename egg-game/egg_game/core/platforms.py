# -*- coding: utf-8 -*-
"""Modelos de cestas (plataformas one-way) e ninho final."""

from __future__ import annotations

import math
from dataclasses import dataclass

from egg_game.core.constants import (
    CENTER_X,
    DEFAULT_BASKET_WIDTH,
    PLAYABLE_MAX_X,
    PLAYABLE_MIN_X,
)


@dataclass
class Platform:
    """
    Representa uma cesta ou o ninho final no mundo do jogo (SPEC §0.3).
    Suporta movimento deslizante constante ('slide') com rebote nas bordas
    e movimento harmônico ('oscillating'), além de plataforma inicial ('start')
    e ninho final ('nest').
    """

    id: str
    kind: str  # "start", "slide", "oscillating", "nest"
    x: float
    y: float
    width: float = DEFAULT_BASKET_WIDTH
    min_x: float = PLAYABLE_MIN_X
    max_x: float = PLAYABLE_MAX_X
    speed: float = 0.0          # px/s (para slide) ou velocidade linear base (para oscillating)
    direction: float = 1.0      # +1.0 ou -1.0 (para slide)
    center_x: float = CENTER_X  # Centro de oscilação
    amplitude: float = 0.0      # Amplitude de oscilação (px)
    phase: float = 0.0          # Fase inicial (rad)
    elapsed: float = 0.0        # Tempo acumulado (s)
    visual_variant: str = "basket_static_01"
    vx: float = 0.0             # Velocidade instantânea no eixo X (px/s)

    @property
    def left(self) -> float:
        """Limite esquerdo da superfície útil de pouso."""
        return self.x - self.width * 0.5

    @property
    def right(self) -> float:
        """Limite direito da superfície útil de pouso."""
        return self.x + self.width * 0.5

    @property
    def is_nest(self) -> bool:
        """Indica se esta plataforma é o ninho final de vitória."""
        return self.kind == "nest"

    def position_at(self, dt_from_now: float) -> float:
        """
        Calcula deterministicamente a posição X do centro da plataforma
        após `dt_from_now` segundos a partir do estado atual.
        """
        if dt_from_now <= 0.0 or self.speed == 0.0:
            return self.x

        if self.kind == "slide":
            span = max(1.0, self.max_x - self.min_x)
            # Representa o movimento de ping-pong (rebote) em [min_x, max_x]
            offset_inicial = (self.x - self.min_x) if self.direction >= 0 else (2.0 * span - (self.x - self.min_x))
            total = (offset_inicial + self.speed * dt_from_now) % (2.0 * span)
            if total <= span:
                return self.min_x + total
            return self.max_x - (total - span)

        if self.kind == "oscillating" and self.amplitude > 0.0:
            omega = self.speed / self.amplitude
            t_futuro = self.elapsed + dt_from_now
            return self.center_x + self.amplitude * math.sin(omega * t_futuro + self.phase)

        return self.x

    def step(self, dt: float) -> float:
        """
        Avança o movimento horizontal da plataforma por `dt` segundos.
        Retorna o deslocamento `dx` ocorrido neste passo.
        """
        if dt <= 0.0:
            self.vx = 0.0
            return 0.0

        x_anterior = self.x
        self.elapsed += dt

        if self.kind == "slide" and self.speed > 0.0:
            novo_x = self.x + self.direction * self.speed * dt
            if novo_x > self.max_x:
                excesso = novo_x - self.max_x
                novo_x = self.max_x - excesso
                self.direction = -1.0
            elif novo_x < self.min_x:
                excesso = self.min_x - novo_x
                novo_x = self.min_x + excesso
                self.direction = 1.0
            self.x = max(self.min_x, min(self.max_x, novo_x))

        elif self.kind == "oscillating" and self.amplitude > 0.0 and self.speed > 0.0:
            omega = self.speed / self.amplitude
            self.x = self.center_x + self.amplitude * math.sin(omega * self.elapsed + self.phase)

        dx = self.x - x_anterior
        self.vx = dx / dt
        return dx
