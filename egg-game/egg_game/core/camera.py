# -*- coding: utf-8 -*-
"""Câmera vertical que acompanha a subida do ovo (PRD §10.1 e SPEC §0)."""

from __future__ import annotations

from dataclasses import dataclass

from egg_game.core.constants import CENTER_X, LOGICAL_H, START_WORLD_Y


@dataclass
class VerticalCamera:
    """
    Câmera que acompanha o ovo apenas durante a subida (nunca desce nas quedas)
    e mantém o ovo horizontalmente centrado na tela lógica (`screen_x = CENTER_X`).
    """

    y: float = START_WORLD_Y - LOGICAL_H * 0.72
    screen_h: int = LOGICAL_H
    follow_ratio: float = 0.42

    def reset(self, start_world_y: float = START_WORLD_Y) -> None:
        """Reposiciona a câmera para o início da partida."""
        self.y = start_world_y - self.screen_h * 0.72

    def update(self, player_world_y: float) -> None:
        """
        Atualiza `self.y` caso o ovo supere a linha de acompanhamento (42% da altura).
        Como `world_y` diminui ao subir, usamos `min()`.
        """
        alvo_y = player_world_y - self.follow_ratio * self.screen_h
        if alvo_y < self.y:
            self.y = alvo_y

    def world_to_screen_y(self, world_y: float) -> float:
        """Converte coordenada Y de mundo para coordenada Y de tela."""
        return world_y - self.y

    def world_to_screen_x(self, world_x: float, player_world_x: float) -> float:
        """
        Converte coordenada X de mundo para coordenada X de tela mantendo o ovo
        sempre centrado em `CENTER_X` (`LOGICAL_W / 2`), conforme SPEC §0 e §0.2.
        """
        return (world_x - player_world_x) + CENTER_X

    @property
    def bottom_limit_y(self) -> float:
        """Limite inferior da câmera abaixo do qual a queda aciona game over."""
        return self.y + self.screen_h + 70.0
