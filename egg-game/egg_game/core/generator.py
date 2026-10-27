# -*- coding: utf-8 -*-
"""Gerador determinístico de cestas e validador de alcançabilidade (SPEC §0.4)."""

from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

from egg_game.core.constants import (
    CENTER_X,
    DEFAULT_BASKET_WIDTH,
    DEFAULT_SEED,
    GRAVITY,
    JUMP_IMPULSE,
    MAX_DELTA_Y,
    MIN_DELTA_Y,
    MIN_TIMING_WINDOW_S,
    NEST_WIDTH,
    NEST_WORLD_Y,
    PIXELS_PER_METER,
    PLAYABLE_MAX_X,
    PLAYABLE_MIN_X,
    START_WORLD_Y,
)
from egg_game.core.platforms import Platform

VARIANTES_VISUAIS_CESTAS = (
    "basket_static_01",
    "basket_leaves_01",
    "basket_leaves_02",
)


def flight_time_for_delta_y(delta_y: float) -> Optional[float]:
    """
    Calcula o tempo de voo `t_land` (na fase descendente, `vy > 0`) para um salto
    que parte de `y_origem` e atinge `y_alvo = y_origem - delta_y`.
    Equação: -delta_y = v0 * t + 0.5 * g * t²  =>  0.5*g*t² + v0*t + delta_y = 0.
    """
    if delta_y <= 0.0:
        return None
    v0 = JUMP_IMPULSE  # negativo (-950)
    g = GRAVITY        # positivo (2400)
    discriminante = (v0 * v0) - 2.0 * g * delta_y
    if discriminante <= 1e-5:
        return None
    raiz = math.sqrt(discriminante)
    return (-v0 + raiz) / g


class ReachabilityValidator:
    """
    Verifica se existe uma janela temporal `>= min_window_s` em que um pulo
    a partir da cesta âncora aterrissa com segurança na cesta-alvo (SPEC §0.4).
    """

    @staticmethod
    def can_land_if_jump_after(
        anchor: Platform,
        target: Platform,
        delay_s: float = 0.0,
        margin_ratio: float = 0.38,
    ) -> bool:
        """Verifica se pular após `delay_s` segundos resulta em pouso válido em `target`."""
        delta_y = anchor.y - target.y
        t_voo = flight_time_for_delta_y(delta_y)
        if t_voo is None:
            return False

        x_decolagem = anchor.position_at(delay_s)
        x_alvo_no_pouso = target.position_at(delay_s + t_voo)
        tolerancia_x = target.width * margin_ratio
        return abs(x_decolagem - x_alvo_no_pouso) <= tolerancia_x

    @classmethod
    def compute_timing_window(
        cls,
        anchor: Platform,
        target: Platform,
        probe_duration_s: float = 3.6,
        dt_probe_s: float = 0.02,
    ) -> Tuple[bool, float, Optional[float]]:
        """
        Amostra instantes de pulo em `[0, probe_duration_s]` e calcula a maior
        janela contínua de tempo em que o salto alcança `target`.
        Retorna `(alcançavel, maior_janela_s, melhor_instante_s)`.
        """
        delta_y = anchor.y - target.y
        t_voo = flight_time_for_delta_y(delta_y)
        if t_voo is None:
            return (False, 0.0, None)

        passos = int(probe_duration_s / dt_probe_s)
        janela_atual = 0.0
        maior_janela = 0.0
        melhor_t: Optional[float] = None
        inicio_janela = 0.0

        for i in range(passos + 1):
            t_pulo = i * dt_probe_s
            if cls.can_land_if_jump_after(anchor, target, t_pulo, margin_ratio=0.40):
                if janela_atual == 0.0:
                    inicio_janela = t_pulo
                janela_atual += dt_probe_s
                if janela_atual > maior_janela:
                    maior_janela = janela_atual
                    melhor_t = inicio_janela + janela_atual * 0.5
            else:
                janela_atual = 0.0

        return (maior_janela >= MIN_TIMING_WINDOW_S, maior_janela, melhor_t)


class LevelGenerator:
    """
    Gerador determinístico de cestas para o modo Aventura (0 a 120 m).
    Garante que toda cesta gerada passe pelo `ReachabilityValidator`.
    """

    def __init__(self, seed: int = DEFAULT_SEED, target_nest_y: float = NEST_WORLD_Y) -> None:
        self.seed = int(seed)
        self.rng = random.Random(self.seed)
        self.target_nest_y = float(target_nest_y)
        self.counter = 0

    def _next_id(self, prefix: str = "b") -> str:
        self.counter += 1
        return f"{prefix}-{self.counter:04d}"

    def create_start_platform(self, start_y: float = START_WORLD_Y) -> Platform:
        """Cria a cesta inicial centrada, com slide suave para ensinar o timing."""
        return Platform(
            id=self._next_id("start"),
            kind="slide",
            x=CENTER_X,
            y=start_y,
            width=152.0,
            min_x=CENTER_X - 70.0,
            max_x=CENTER_X + 70.0,
            speed=36.0,
            direction=1.0,
            center_x=CENTER_X,
            visual_variant="basket_static_01",
        )

    def generate_up_to(
        self,
        platforms: List[Platform],
        min_world_y: float,
    ) -> List[Platform]:
        """
        Gera novas plataformas acima da última plataforma da lista até atingir
        `min_world_y` ou o ninho final (`self.target_nest_y`).
        """
        if not platforms:
            platforms.append(self.create_start_platform())

        while True:
            ancora = min(platforms, key=lambda p: p.y)
            if ancora.is_nest or ancora.y <= min_world_y:
                break

            distancia_ate_ninho = ancora.y - self.target_nest_y
            if distancia_ate_ninho <= MAX_DELTA_Y:
                # Coloca o ninho final garantidamente alcançável
                y_ninho = max(self.target_nest_y, ancora.y - 115.0)
                ninho = Platform(
                    id=self._next_id("nest"),
                    kind="nest",
                    x=CENTER_X,
                    y=y_ninho,
                    width=NEST_WIDTH,
                    min_x=CENTER_X - 40.0,
                    max_x=CENTER_X + 40.0,
                    speed=0.0,
                    center_x=CENTER_X,
                    visual_variant="nest_final",
                )
                platforms.append(ninho)
                break

            nova_cesta = self._generate_next_reachable_platform(ancora)
            platforms.append(nova_cesta)

        return platforms

    def _generate_next_reachable_platform(self, anchor: Platform) -> Platform:
        """Amostra e valida uma nova cesta acima de `anchor`."""
        altura_m = max(0.0, (START_WORLD_Y - anchor.y) / PIXELS_PER_METER)
        progresso = min(1.0, altura_m / 120.0)

        for tentativa in range(40):
            delta_y = self.rng.uniform(MIN_DELTA_Y, MAX_DELTA_Y)
            novo_y = anchor.y - delta_y
            if novo_y - self.target_nest_y < MIN_DELTA_Y and novo_y > self.target_nest_y:
                novo_y = self.target_nest_y + MIN_DELTA_Y

            tipo = "slide" if self.rng.random() < 0.55 else "oscillating"
            largura = DEFAULT_BASKET_WIDTH - progresso * 14.0
            vel_base = 55.0 + progresso * 95.0 + self.rng.uniform(-12.0, 18.0)
            variante = self.rng.choice(VARIANTES_VISUAIS_CESTAS)

            if tipo == "slide":
                alcance = 110.0 + progresso * 70.0
                min_x = max(PLAYABLE_MIN_X, CENTER_X - alcance)
                max_x = min(PLAYABLE_MAX_X, CENTER_X + alcance)
                x_ini = self.rng.uniform(min_x, max_x)
                direcao = 1.0 if self.rng.random() < 0.5 else -1.0
                candidata = Platform(
                    id=self._next_id("b"),
                    kind="slide",
                    x=x_ini,
                    y=novo_y,
                    width=largura,
                    min_x=min_x,
                    max_x=max_x,
                    speed=vel_base,
                    direction=direcao,
                    center_x=CENTER_X,
                    visual_variant=variante,
                )
            else:
                amplitude = 85.0 + progresso * 65.0
                fase = self.rng.uniform(0.0, 2.0 * math.pi)
                x_ini = CENTER_X + amplitude * math.sin(fase)
                candidata = Platform(
                    id=self._next_id("b"),
                    kind="oscillating",
                    x=x_ini,
                    y=novo_y,
                    width=largura,
                    min_x=CENTER_X - amplitude,
                    max_x=CENTER_X + amplitude,
                    speed=vel_base,
                    center_x=CENTER_X,
                    amplitude=amplitude,
                    phase=fase,
                    visual_variant=variante,
                )

            ok, _, _ = ReachabilityValidator.compute_timing_window(anchor, candidata)
            if ok:
                return candidata

        # Fallback conservador caso todas as amostras aleatórias falhem:
        # cesta centrada com oscilação moderada sobre o mesmo centro da âncora
        return Platform(
            id=self._next_id("b"),
            kind="slide",
            x=CENTER_X,
            y=anchor.y - 105.0,
            width=DEFAULT_BASKET_WIDTH,
            min_x=CENTER_X - 95.0,
            max_x=CENTER_X + 95.0,
            speed=62.0,
            direction=1.0,
            center_x=CENTER_X,
            visual_variant="basket_static_01",
        )
